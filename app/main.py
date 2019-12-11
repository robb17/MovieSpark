# necessary for spawning new threads without getting deleted by the background thread
import eventlet
eventlet.monkey_patch()

from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from . import db
import os, sys
from . import socketio
from app import app
import time
import random
import requests

from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.schema import Index

from .init_scripts import init_weights, get_movies, get_genres, get_tags_and_relevancy, get_scored_tags

from .models import Movie, Genre, Tag, TagWeight, RelevanceWeight

SAMPLE_SIZE = 1000

main = Blueprint('main', __name__)

basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine('sqlite:///' + os.path.join(basedir, 'db.sqlite'))

@socketio.on('feedback')
def handle_feedback(data):
    query_input = data['query_input']
    query_type = data['query_type']
    suggested_movie_title = data['suggested_movie']
    upvote = True if data['upvote'] == 'yes' else False
    if query_type == 'Movie':
        queried_movie = db.session.query(Movie).filter(Movie.name.ilike(query_input)).first()
        suggested_movie = db.session.query(Movie).filter(Movie.name.ilike(suggested_movie_title)).first()
        if not queried_movie or not suggested_movie:
            socketio.emit('feedback response', {"text": "Sorry, movie not found", "movie_title": suggested_movie_title}, room=request.sid)
            return
        current_offset = RelevanceWeight.query.filter(RelevanceWeight.movie_key == queried_movie.movie_id, RelevanceWeight.movie_referenced == suggested_movie.movie_id).first()
        if not current_offset:
            current_offset = RelevanceWeight.query.filter(RelevanceWeight.movie_key == queried_movie.movie_id, RelevanceWeight.movie_referenced == suggested_movie.movie_id).first()
        if current_offset:
            new_value = max(-10000, current_offset.offset - 100) if upvote else min(10000, current_offset.offset + 100)
            current_offset.offset = new_value # more relevant = less diff
        else:
            offset = -100 if upvote else 100
            new_offset = RelevanceWeight(movie_key=queried_movie.movie_id, movie_referenced=suggested_movie.movie_id, offset=offset)
            db.session.add(new_offset)
        db.session.commit()
        socketio.emit('feedback response', {"text": "Thanks for your feedback!", "movie_title": suggested_movie_title}, room=request.sid)
        return
    else:
        queried_tag = db.session.query(Tag).filter(Tag.name == query_input).first()
        suggested_movie = db.session.query(Movie).filter(Movie.name.ilike(suggested_movie_title)).first()
        if not queried_tag or not suggested_movie:
            socketio.emit('feedback response', {"text": "Sorry, movie not found", "movie_title": suggested_movie_title}, room=request.sid)
            return
        tagweight = db.session.query(TagWeight).filter(TagWeight.tag_id == queried_tag.tag_id, TagWeight.movie_id == suggested_movie.movie_id).first()
        temp_weight = min(tagweight.weight + 100, 10000) if upvote else max(tagweight.weight - 100, 0)
        tagweight.weight = temp_weight
        db.session.commit()
        socketio.emit('feedback response', {"text": "Thanks for your feedback!", "movie_title": suggested_movie_title}, room=request.sid)
        return

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
    print("query request received")
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
    in_depth_details = [["" for x in range(0, 6)] for y in range(0, 3)]

    it = 0
    for suggestion in suggestions:
        movie = db.session.query(Movie).filter(Movie.name.ilike(suggestion)).first()
        genres = ""
        year = ""
        if movie:
            for genre in movie.genres:
                genres += str(genre.name) + ", "
            genres = genres[:-2]
            year = movie.year_released
        in_depth_details[it][1] = suggestion
        in_depth_details[it][4] = year
        in_depth_details[it][5] = genres
        it += 1

    socketio.emit('query result', in_depth_details, room=request.sid)

    it = 0
    for suggestion in suggestions:
        plot = ""
        poster = ""
        cast = ""
        parameters = {
            't': suggestion
        }
        response = requests.get("http://www.omdbapi.com/?i=tt3896198&apikey=e35c922", params=parameters)

        #create a tuple 
        jversion = response.json()
        try: 
            plot = jversion['Plot']
        except Exception as e:
            pass
        try: 
            poster = jversion['Poster']
        except Exception as e:
            pass
        try:
            cast = jversion['Actors']
        except Exception as e:
            pass
        attrList = [poster, suggestion, plot, cast, year, genres]
        # append it to the list of tuples
        in_depth_details[it][0] = poster
        in_depth_details[it][1] = suggestion
        in_depth_details[it][2] = plot
        in_depth_details[it][3] = cast
        it += 1

    print("query complete")
    socketio.emit('query result', in_depth_details, room=request.sid)

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

    for movie in random.sample(movies, 1800):
        if (movie.movie_id == search_movie.movie_id):
            continue
        diff = 0
        test_list = [int(row[0]) for row in conn.execute('SELECT weight FROM movie, tagweight WHERE movie.movie_id = ' + str(movie.movie_id) + ' AND tagweight.movie_id = movie.movie_id')]

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

def bubble_up_new_movie(movie, weight, matches):
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


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')

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

    print("adding index")
    try:
        index_tag_movie = Index('index_tag_movie', TagWeight.tag_id, TagWeight.movie_id)
        index_tag_movie.create(bind=engine)
    except Exception as e:
        print("index could not be created, probably because it already exists")
