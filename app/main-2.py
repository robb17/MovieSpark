from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from . import db
import os, sys
from . import socketio
from app import app
import time
import random

from sqlalchemy import create_engine
from sqlalchemy.sql import text

from multiprocessing import Pool

from .init_scripts import init_weights, get_movies, get_genres, get_tags_and_relevancy, get_scored_tags

from .models import Movie, Genre, Tag, TagWeight, RelevanceWeight

main = Blueprint('main', __name__)

basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite'))

@socketio.on('autofill request')
def search(data):
    user_input = data['query_text']
    query_type = data['query_type']
    return_str = ""
    user_input = user_input.lower()
    if ((len(user_input) > 3) and (user_input[0:4] == 'the ')):
        user_input = user_input[4:]
    input = "%" + user_input + "%"
    return_str, results = test_for_empty_result(query_type, input)
    if results:
        return_str = 'Are you thinking of <span style="cursor: pointer; text-decoration: underline; color: blue;" id="search_suggestion">' + str(results.name) + '</span>?'
    socketio.emit('title result', return_str, room=request.sid)

def test_for_empty_result(query_type, final_input):
    results = None
    return_str = ""
    if query_type == 'Movie':
        results = db.session.query(Movie).filter(Movie.name.ilike(final_input)).first()
    else:
        results = db.session.query(Tag).filter(Tag.name.ilike(final_input)).first()
    if not results:
        return_str = ["No results found"]
    return (return_str, results)

@socketio.on('query request')
def find_suggestions(data):
    user_input = data['query_text']
    query_type = data['query_type']
    suggestions = None
    return_str, results = test_for_empty_result(query_type, user_input)
    if not results:
        socketio.emit('query result', return_str, room=request.sid)
        return
    if query_type == 'Movie':
        suggestions = movie_to_suggestions(results)
    else:
        suggestions = tag_to_suggestions(results)
    socketio.emit('query result', suggestions, room=request.sid)

def make_tag_list(movie) :
    conn = engine.connect()
    test_list = [int(row[0]) for row in conn.execute('SELECT weight FROM movie, tagweight WHERE movie.movie_id = ' + str(movie.movie_id) + ' AND tagweight.movie_id = movie.movie_id')]
    conn.close()
    return test_list

def movie_to_suggestions(search_movie):
    conn = engine.connect()
    movies = Movie.query.all()
    search_list = [int(row[0]) for row in conn.execute('SELECT weight FROM movie, tagweight WHERE movie.movie_id = ' + str(search_movie.movie_id) + ' AND tagweight.movie_id = movie.movie_id')]
    matches = [[-1, float("inf")], [-1, float("inf")], [-1, float("inf")]]
    relevance_adjustments = RelevanceWeight.query.all()
    adjustment_dict = {}
    for adjustment in relevance_adjustments:
        adjustment_dict[adjustment.movie_key] = [adjustment.movie_referenced, adjustment.offset]
        adjustment_dict[adjustment.movie_referenced] = [adjustment.movie_key, adjustment.offset]
        
    movie_list = random.sample(movies, 2500)
    pool = Pool(processes=8)
    results = pool.map(make_tag_list, movie_list)
    print("Threads complete")
        
    for i in range(0,2000):
        movie = movie_list[i]
        if (movie.movie_id == search_movie.movie_id):
            continue
        diff = 0
        test_list = results[i]

        for i in range(0, 1128) :
            diff += abs(search_list[i] - test_list[i])
        avg_diff = diff / 1128
        diff = 0
        for i in range(0, 1128) :
            if (abs(search_list[i] - test_list[i]) > avg_diff) :
                diff += abs(search_list[i] - test_list[i])
        diff = int((diff / 1128) * 10000)
        if adjustment_dict.get(movie.movie_id):
            diff += adjustment_dict[movie.movie_id][1]
        if (diff < matches[2][1]):
            x = 1
            for match in matches:
                if diff < match[1]:
                    temp_movie = match[0]
                    temp_diff = match[1]
                    match[0] = movie
                    match[1] = diff
                    for match in matches[x:]:
                        second_temp_movie = match[0]
                        second_temp_diff = match[1]
                        match[0] = temp_movie
                        match[1] = temp_diff
                        temp_movie = second_temp_movie
                        temp_diff = second_temp_diff
                    break
                x += 1
    conn.close()
    return [pair[0].name for pair in matches]

def tag_to_suggestions(tag) :
    tag_id = tag.tag_id
    movies = Movie.query.all()
    matches = [[-1, float(-1)], [-1, float(-1)], [-1, float(-1)]]
    for movie in random.sample(movies, 2000):
        this_tag = db.session.query(TagWeight).filter(TagWeight.movie_id == movie.movie_id, TagWeight.tag_id == tag_id).first()
        weight = this_tag.weight
        if (weight > matches[2][1]):
            x = 1
            for match in matches:
                if weight > match[1]:
                    temp_movie = match[0]
                    temp_weight = match[1]
                    match[0] = movie
                    match[1] = weight
                    for match in matches[x:]:
                        second_temp_movie = match[0]
                        second_temp_weight = match[1]
                        match[0] = temp_movie
                        match[1] = temp_weight
                        temp_movie = second_temp_movie
                        temp_weight = second_temp_weight
                    break
                x += 1
    return [pair[0].name for pair in matches]


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/init')
def init():
    init_db()
    flash("Successfully initialized database!")
    return render_template('index.html')

def init_db():
    movies_in_db = db.session.query(Movie).count()
    genres_in_db = db.session.query(Genre).count()
    tags_in_db = db.session.query(Tag).count()
    tagweights_in_db = db.session.query(TagWeight).count()

    print("finding a good basis set...")
    raw_movies = get_movies()
    print("narrowing basis set down to movies with tags...")
    movie_tag_dictionary = get_tags_and_relevancy(raw_movies)
    movies = []
    for movie in raw_movies:
        if movie_tag_dictionary.get(movie[0]):
            movies.append(movie)

    if movies_in_db == 0 or genres_in_db == 0:
        print("populating genres table...")
        genres = get_genres(movies)
        if genres_in_db == 0:
            for i in range(0, len(genres)):
                genre = genres[i]
                new_genre = Genre(genre_id=i, name=genre)
                db.session.add(new_genre)
        db.session.commit()
        print("populating movies table...")
        if movies_in_db == 0:
            for movie in movies:
                new_movie = Movie(movie_id=movie[0], name=movie[1], rating=int(movie[4] * 10000), year_released=movie[2])
                db.session.add(new_movie)
                for genre in movie[3]:
                    stored_genre = Genre.query.filter_by(name=genre).first()
                    new_movie.genres.append(stored_genre)
        print("there are " + str(len(movies)) + " movies in the database")
        db.session.commit()

    if tags_in_db == 0:
        print("populating tags table...")
        tag_dict = get_scored_tags()
        for tag_id in tag_dict.keys():
            new_tag = Tag(tag_id=tag_id, name=tag_dict[tag_id])
            db.session.add(new_tag)
        db.session.commit()

    if tagweights_in_db == 0:
        print("connecting tagweights to movies and tags...")
        movie_count = 1
        start = time.time()
        tag_dict = get_scored_tags()
        for movie_id in movie_tag_dictionary.keys():
            count = 1
            movie = Movie.query.filter_by(movie_id=movie_id).first()
            tagweight_lst = []
            for tag_relevancy in movie_tag_dictionary[movie_id]:
                tagweight = TagWeight(movie_id=movie_id, tag_id=count, weight=tag_relevancy)
                tagweight_lst.append(tagweight)
                count += 1
            db.session.add_all(tagweight_lst)
            movie_count += 1
            if movie_count % 50 == 0:
                print("processing tags for movie " + str(movie_count) + "...")
                print(time.time() - start)
                start = time.time()
        db.session.commit()
