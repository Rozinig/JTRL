from flask_login import UserMixin
from datatime impor datetime
from . import db

class User(UserMixin, db.Model):
        __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))
    emailauth = db.Column(db.Integer)
    authdate = db.Column(db.DateTime(), default=datetime.datetime(1991,1,1))
    currentlang =                                   db.Column(db.String(10))
    nativelang =                                    db.Column(db.String(10))
    targetlangs =                                   db.Column(db.String(10))
    settings = db.Column(db.String(1000))
    created_on =db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    streakdays = db.Column(db.Integer, default=0)
    streakdate = db.Column(d.DateTime(), default=datetime.datetime(1991,1,1))
    totalsentences = db.Column(db.Integer, default=0)
    streakgoal = db.Column(db.Integer, default=10)
    streaknum = db.Column(db.Integer, default=0)

class lang(db.Model):
        __tablename__ = 'langs'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4))
    text = db.Column(db.String(15))
    target = db.Column(db.Boolean, default=True)
    native = db.Column(db.Boolean, default=False)


class sentence(db.Model):
        __tablename__ = 'sentences'
    id = db.Column(db.Integer, primary_key=True)
    #tatoeba_id = db.Column(db.Integer, unique=True)
    lang =                                              db.Column(db.String(4))
    text = db.Column(db.String(255), default= None)
    json = db.Column(db.String(255), default= None) #this may not be necessary
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

                                                        class sentence_translation(db.Model):
                                                                __tablename__ = 'translations'
                                                            sentence_id = db.Column(db.Integer)
                                                            translation_id = db.Column(db.Integer)

class audio(db.Model):
        __tablename__ = 'audios'
    #id = db.Column(db.Integer, primary_key=True)
    sentence_id = db.Column(db.Integer, primary_key=True)
    audio_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100))
    license = db.Column(db.String(100), nullable=False)
    attribution_url = db.Column(db.String(100))

'''class tag(db.Model):
        __tablename__ = 'tags'
    sentence_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(100))'''

class lemma(db.Model):
        __tablename__ = 'lemmas'
    id = db.Column(db.Integer, primary_key=True)
    lemma = db.Column(db.String(100), nullable=False, unique=True)

                                                        class sentence_lemma(db.Model):
                                                            sentence_id = db.Column(db.Integer)
                                                            lemma_id = db.Column(db.Integer)

class grammar(db.Model):
        __tablename__ = 'grammars'
    id = db.Column(db.Integer, primary_key=True)
    lang =                                              db.Column(db.String(4))
    grammartype = db.Column(db.String(100))
    grammar = db.Column(db.String(100))

                                                        class sentence_grammar(db.Model):
                                                            sentence_id = db.Column(db.Integer)
                                                            grammar_id = db.Column(db.Integer)

class user_lemma(db.Model):
    user_id =                                                   db.Column(db.Integer)
    lemma_id =                                                  db.Column(db.Integer)
    count = db.Column(db.Integer)
    date = db.Column(db.DateTime())

class user_grammar(db.Model):
    user_id =                                                   db.Column(db.Integer)
    grammar_id =                                                db.Column(db.Integer)
    unknown = db.Column(db.Boolean)
    known = db.Column(db.Boolean)
    focus = db.Column(db.Boolean)

class event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime(), default=datetime.utcnow)
    user_id =                                               db.Column(db.Integer)
    sentence_id =                                           db.Column(db.Integer)
    event_type = db.Column(db.String(255))
    event_info = db.Column(db.String(1000))
