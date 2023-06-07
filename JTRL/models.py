from flask_login import UserMixin
from datetime import datetime
from . import db


user_targetlangs = db.Table('user_targetlangs',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('lang_id', db.Integer, db.ForeignKey('langs.id'))
    )
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))
    emailauth = db.Column(db.Integer())
    authdate = db.Column(db.DateTime(), default=datetime(1991,1,1))
    currentlang = db.Column(db.Integer, db.ForeignKey('langs.id'))
    nativelang = db.Column(db.Integer, db.ForeignKey('langs.id'))
    targetlangs = db.relationship('Lang', secondary=user_targetlangs, backref = 'users')
    settings = db.Column(db.String(1000))
    created_on =db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    streakdays = db.Column(db.Integer(), default=0)
    streakdate = db.Column(db.DateTime(), default=datetime(1991,1,1))
    totalsentences = db.Column(db.Integer(), default=0)
    streakgoal = db.Column(db.Integer(), default=10)
    streaknum = db.Column(db.Integer(), default=0)
    events = db.relationship('Event', backref='user')
    lemmas = db.relationship('Lemmainfo', backref='user')

class Lang(db.Model):
    __tablename__ = 'langs'
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(4))
    text = db.Column(db.String(15))
    target = db.Column(db.Boolean, default=True)
    native = db.Column(db.Boolean, default=False)
    user_currentlang = db.relationship('User', backref = 'currentlang')
    user_nativelang = db.relationship('User', backref = 'nativelang')
    texts = db.relationship('Text', backref = 'lang')
    lemmas = db.relationship('Lemma', backref='lang')
    grammar = db.relationship('Grammar', backref = 'lang')
    events = db.relationship('Event', backref='lang')

links = db.Table('links',
    db.Column('text_id', db.Integer, db.ForeignKey('texts.id')),
    db.Column('translation_id', db.Integer, db.ForeignKey('texts.id')))

class Text(db.Model):
    __tablename__ = 'texts'
    id = db.Column(db.Integer(), primary_key=True) # Tatoeba are positive other are negative
    type = db.Column(db.String(255)) # Sentence , paragraph, dialog?
    lang = db.Column(db.Integer, db.ForeignKey('langs.id'))
    text = db.Column(db.Text(), default= None, nullable=False)
    audio = db.relationship('Audio', backref='text')
    #json = db.Column(db.Text(), default= None) #this may not be necessary but nice to have?
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    translations = db.relationship('Text', secondary=links, backref='texts')
    events = db.relationship('Event', backref='text')

class Audio(db.Model):
    __tablename__ = 'audios'
    id = db.Column(db.Integer(), primary_key=True) # Tatoeba are positive other are negative
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    username = db.Column(db.String(100))
    license = db.Column(db.String(100), nullable=False)
    attribution_url = db.Column(db.Text())

'''class tag(db.Model):
    __tablename__ = 'tags'
    text_id = db.Column(db.Integer(), primary_key=True)
    tag_name = db.Column(db.String(100))'''

text_lemma = db.Table('text_lemma',
    db.Column('text_id', db.Integer, db.ForeignKey('texts.id')),
    db.Column('lemma_id', db.Integer, db.ForeignKey('lemmas.id')))

class Lemma(db.Model):
    __tablename__ = 'lemmas'
    id = db.Column(db.Integer(), primary_key=True)
    lang = db.Column(db.Integer, db.ForeignKey('langs.id'))
    lemma = db.Column(db.String(100), nullable=False)
    texts = db.relationship('Text', secondary=text_lemma, backref='lemma')
    info_users = db.relationship('Lemmainfo', backref='lemma')

text_grammar = db.Table('text_grammar',
    db.Column('text_id', db.Integer, db.ForeignKey('texts.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id')))

unknown = db.Table('unknown',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id')))

known = db.Table('known',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id')))

focus = db.Table('focus',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id')))

class Grammar(db.Model):
    __tablename__ = 'grammar'
    id = db.Column(db.Integer(), primary_key=True)
    lang = db.Column(db.Integer(), db.ForeignKey('langs.id'))
    grammartype = db.Column(db.String(100))
    grammar = db.Column(db.String(100))
    texts = db.relationship('Text', secondary=text_grammar, backref='grammar')
    users_unknown = db.relationship('User', secondary=unknown, backref='unknown')
    users_known = db.relationship('User', secondary=known, backref='known')
    users_focus = db.relationship('User', secondary=focus, backref='focus')

class Lemmainfo(db.Model):
    __tablename__ = 'lemmainfos'
    #id = db.Column(db.Integer(), primary_key=True) # need to figure out how to remove
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), primary_key=True)
    lemma_id = db.Column(db.Integer(), db.ForeignKey('lemmas.id'), primary_key=True)
    count = db.Column(db.Integer(), default=0)
    date = db.Column(db.DateTime(), default=datetime(1991,1,1), onupdate=datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer(), primary_key=True)
    date_time = db.Column(db.DateTime(), default=datetime.utcnow)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    lang_id = db.Column(db.Integer(), db.ForeignKey('langs.id'))
    text_id = db.Column(db.Integer(), db.ForeignKey('texts.id'))
    event_type = db.Column(db.String(255))
    event_info = db.Column(db.Text())
