from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model): #UserMixin, 
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    emailauth = db.Column(db.Integer)
    authdate = db.Column(db.String(100))
    currentlang = db.Column(db.String(10))
    nativelang = db.Column(db.String(10))
    settings = db.Column(db.String(1000))
    streakdays = db.Column(db.Integer)
    streakdate = db.Column(db.String(100))
    totalsentences = db.Column(db.Integer)
    streakgoal = db.Column(db.Integer)
    streaknum = db.Column(db.Integer)