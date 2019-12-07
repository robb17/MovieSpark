from . import db
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

movie_genre_table = db.Table('movie_genre_table', db.Model.metadata,
	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
	db.Column('genre_id', db.Integer, ForeignKey('genre.genre_id')))

#movie_cast_table = db.Table('movie_cast_table', db.Model.metadata,
#	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
#	db.Column('actor_id', db.Integer, ForeignKey('actor.actor_id')))

relevancy_table = db.Table('relevancy_table', db.Model.metadata,
	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id'), index=True),
	db.Column('referenced_movie_id', db.Integer, ForeignKey('movie.movie_id')),
	db.Column('weight', db.Integer),
	UniqueConstraint('movie_id', 'referenced_movie_id', name='unique_pairing'))

tag_table = db.Table('tag_table', db.Model.metadata,
	db.Column('movie_id', db.Integer, ForeignKey('movie.movie_id')),
	db.Column('tag_id', db.Integer, ForeignKey('tag.tag_id')),
	db.Column('weight', db.Integer))

class Movie(db.Model):
	__tablename__ = 'movie'
	movie_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(1000))
	rating = db.Column(db.Integer)
	year_released = db.Column(db.Integer)
	genres = relationship("Genre", secondary=movie_genre_table, back_populates="movies")
	#cast = relationship("Actor", secondary=movie_cast_table, back_populates="movies")
	tags = relationship("Tag", secondary=tag_table, back_populates="movies")

	# One-to-many relationship here is many-to-many as a result of its self-referential nature
	weights = relationship("Movie", secondary=relevancy_table,
		primaryjoin=movie_id==relevancy_table.c.movie_id,
		secondaryjoin=movie_id==relevancy_table.c.referenced_movie_id)

class Genre(db.Model):
	__tablename__ = 'genre'
	genre_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(1000))
	# Name should be constrained to one of a dictionary of values
	movies = relationship("Movie", secondary=movie_genre_table, back_populates="genres")

class Tag(db.Model):
	__tablename__ = 'tag'
	tag_id = db.Column(db.Integer, primary_key=True)
	tag = db.Column(db.String(5000))
	movies = relationship("Movie", secondary=tag_table, back_populates="tags")

#class Actor(db.Model):
#	__tablename__ = 'actor'
#	actor_id = db.Column(db.Integer, primary_key=True)
#	name = db.Column(db.String(300))
#	movies = relationship("Movie", secondary=movie_cast_table, back_populates="cast")
