from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model): #UserMixin, 
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    emailauth = db.Column(db.Integer)
    authdate = db.Column(db.String(100))