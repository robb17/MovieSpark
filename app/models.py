from . import db
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

movie_genre_table = db.Table('movie_genre_table', db.Model.metadata,
	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
	db.Column('genre_id', db.Integer, ForeignKey('genre.genre_id')))

#movie_cast_table = db.Table('movie_cast_table', db.Model.metadata,
#	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
#	db.Column('actor_id', db.Integer, ForeignKey('actor.actor_id')))

#relevance_table = db.Table('relevance_table', db.Model.metadata,
#	db.Column('movie_key', db.Integer, ForeignKey('movie.movie_id')),
#	db.Column('offset', db.Integer),
#	db.Column('movie_referenced', db.Integer, ForeignKey('movie.movie_id')))

#tag_table = db.Table('tag_table', db.Model.metadata,
#	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
#	db.Column('tagweight_id', db.Integer, ForeignKey('tagweight.tagweight_id')),
#	db.Column('tag_id', db.Integer, ForeignKey('tag.tag_id')))

class RelevanceWeight(db.Model):
	__tablename__ = 'relevance'
	relevance_id = db.Column(db.Integer, primary_key=True)
	movie_key = db.Column(db.Integer, db.ForeignKey('movie.movie_id'))
	movie_referenced = db.Column(db.Integer, db.ForeignKey('movie.movie_id'))
	offset = db.Column(db.Integer)

class Movie(db.Model):
	__tablename__ = 'movie'
	movie_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(1000))
	rating = db.Column(db.Integer)
	year_released = db.Column(db.Integer)
	genres = relationship("Genre", secondary=movie_genre_table, back_populates="movies")
	#cast = relationship("Actor", secondary=movie_cast_table, back_populates="movies")

class Genre(db.Model):
	__tablename__ = 'genre'
	genre_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(1000))
	movies = relationship("Movie", secondary=movie_genre_table, back_populates="genres")

class TagWeight(db.Model):
	__tablename__ = 'tagweight'
	movie_id = db.Column(db.Integer, db.ForeignKey('movie.movie_id'), primary_key=True)
	tag_id = db.Column(db.Integer, db.ForeignKey('tag.tag_id'), primary_key=True)
	weight = db.Column(db.Integer)

class Tag(db.Model):
	__tablename__ = 'tag'
	tag_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(5000))

#class Actor(db.Model):
#	__tablename__ = 'actor'
#	actor_id = db.Column(db.Integer, primary_key=True)
#	name = db.Column(db.String(300))
#	movies = relationship("Movie", secondary=movie_cast_table, back_populates="cast")
