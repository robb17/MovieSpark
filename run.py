from app import db

from app import create_app
db.create_all(app=create_app())