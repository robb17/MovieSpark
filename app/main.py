from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from . import db
import os, sys
from . import socketio
from app import app

from .init_scripts import init_weights, get_movies, get_genres, get_tags_and_relevancy, get_scored_tags

from .models import Movie, Genre, Tag, TagWeight

main = Blueprint('main', __name__)

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
	movies = get_movies()

	if movies_in_db == 0 or genres_in_db == 0:
		genres = get_genres(movies)
		if genres_in_db == 0:
			for i in range(0, len(genres)):
				genre = genres[i]
				new_genre = Genre(genre_id=i, name=genre)
				db.session.add(new_genre)
		db.session.commit()
		print("successfully added genres")
		if movies_in_db == 0:
			for movie in movies:
				new_movie = Movie(movie_id=movie[0], name=movie[1], rating=int(movie[4] * 10000), year_released=movie[2])
				db.session.add(new_movie)
				for genre in movie[3]:
					stored_genre = Genre.query.filter_by(name=genre).first()
					new_movie.genres.append(stored_genre)
		print("successfully added movies")
		db.session.commit()

	if tags_in_db == 0:
		tag_dict = get_scored_tags()
		for tag_id in tag_dict.keys():
			new_tag = Tag(tag_id=tag_id, tag=tag_dict[tag_id])
			db.session.add(new_tag)
		db.session.commit()
		print("successfully added tags")

	if tagweights_in_db < 100000:
		print("adding tag weights")
		print("collecting tag relevancy data for movies used in database")
		movie_dict = get_tags_and_relevancy(movies)
		print("done collecting tag relevancy data")
		tagweight_id_counter = 1
		tag_list = []
		n_tags = len(get_scored_tags())
		print("caching tags")
		for x in range(1, n_tags + 1):				# get a pointer to each tag so we don't have to constantly re-look them up
			tag_list.append(Tag.query.filter_by(tag_id=x).first())
		print("adding tagweights to database")
		for movie_id in movie_dict.keys():
			count = 1
			movie = Movie.query.filter_by(movie_id=movie_id).first()
			for tag_relevancy in movie_dict[movie_id]:
				if tagweight_id_counter < 100:
					print(tag_relevancy)
				new_tagweight = TagWeight(tagweight_id=tagweight_id_counter, weight=tag_relevancy)
				db.session.add(new_tagweight)
				tag = tag_list[count - 1]
				new_tagweight.movie.append(movie)
				new_tagweight.tag.append(tag)
				count += 1
				tagweight_id_counter += 1
				if tagweight_id_counter % 10000 == 0:
					print("adding tagweight = " + str(tagweight_id_counter))
		print("successfully added tag weights")
		db.session.commit()
