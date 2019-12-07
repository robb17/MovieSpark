from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from .models import Movie, Genre, Tag
from . import db
import os, sys
from . import socketio
from app import app

from .init_scripts import init_weights
from .init_scripts import get_movies
from .init_scripts import get_genres
from .models import Movie, Genre, Tag

main = Blueprint('main', __name__)

@main.route('/')
def index():
	return render_template('index.html')

@main.route('/init')
def init():
	add_movies()
	return render_template('index.html')

def add_movies():
    movies = get_movies()
    genres = get_genres(movies)
    for i in range(0, len(genres)):
        genre = genres[i]
        new_genre = Genre(genre_id=i, name=genre)
        db.session.add(new_genre)
    for movie in movies:
        new_movie = Movie(movie_id=movie[0], name=movie[1], rating=int(movie[4] * 10000), year_released=movie[2])
        db.session.add(new_movie)
        for genre in movie[3]:
            stored_genre = Genre.query.filter_by(name=genre).first()
            new_movie.genres.append(stored_genre)
    db.session.commit()