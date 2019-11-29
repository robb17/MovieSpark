from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os, sys
from flask_socketio import SocketIO

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()
app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet", manage_session=False)
socketio.init_app(app)

def page_not_found(e):
    return render_template('404.html'), 404

def create_app():
    app.register_error_handler(404, page_not_found)

    app.config['SECRET_KEY'] = 'e790f108ca10af2b13c39b51428279b9ceba79786c0a596e'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')

    db.init_app(app)

    #sys.path.insert(0, os.path.abspath('..'))
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    app.static_folder = 'static'

    socketio.run(app, debug=True)

    return app