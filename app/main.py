from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from .models import Movie, Genre, Tag, Actor
from . import db
import os, sys
from . import socketio
from app import app

main = Blueprint('main', __name__)

@main.route('/')
def index():
	return render_template('index.html')