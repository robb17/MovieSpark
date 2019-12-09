from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from . import db
import os, sys
from . import socketio
from app import app
import time

from .init_scripts import init_weights, get_movies, get_genres, get_tags_and_relevancy, get_scored_tags

from .models import Movie, Genre, Tag, TagWeight

main = Blueprint('main', __name__)

@socketio.on('search request')
def search(user_input):
	return_str = ""
    user_input = user_input.lower()
    if ((len(user_input) > 3) and (user_input[0:4] == 'the ')):
        user_input = user_input[4:]
    input = "%" + user_input + "%"
    movie = db.session.query(Movie).filter(Movie.name.ilike(input)).first()
    if not movie:
        return_str = "No results found"
    else:
    	return_str = "Did you mean " + str(movie.name) + "?"
    socketio.emit('search result', return_str, room=request.sid)

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
			new_tag = Tag(tag_id=tag_id, tag=tag_dict[tag_id])
			db.session.add(new_tag)
		db.session.commit()

	if tagweights_in_db == 0:
		tag_list = []
		n_tags = len(get_scored_tags())
		print("caching tags...")
		for x in range(1, n_tags + 1):				# get a pointer to each tag so we don't have to constantly re-look them up
			tag_list.append(Tag.query.filter_by(tag_id=x).first())
		print("populating tagweights table...")
		tagweight_list = []
		for x in range(0, 10001):	# tag weights are quantized: only need 10001 of them!
			new_tagweight = TagWeight(tagweight_id=x, weight=x)
			db.session.add(new_tagweight)
			tagweight_list.append(new_tagweight)
		print("connecting tagweights to movies and tags...")
		movie_count = 1
		start = time.time()
		for movie_id in movie_tag_dictionary.keys():
			count = 1
			movie = Movie.query.filter_by(movie_id=movie_id).first()
			for tag_relevancy in movie_tag_dictionary[movie_id]:
				tag = tag_list[count - 1]
				tagweight = tagweight_list[tag_relevancy]
				tagweight.movie.append(movie)
				tagweight.tag.append(tag)
				count += 1
			movie_count += 1
			if movie_count % 50 == 0:
				print("Processing tags for movie " + str(movie_count) + "...")
				print(time.time() - start)
				start = time.time()
		db.session.commit()
