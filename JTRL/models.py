from flask_login import UserMixin
from datetime import datetime
from . import db


user_targetlangs = db.Table('user_targetlangs',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('lang_code', db.String, db.ForeignKey('langs.code'), primary_key=True)
    )

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True) # primary keys are required by SQLAlchemy
    type = db.Column(db.String(20), default='normal')
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    emailauth = db.Column(db.Integer(), default= 9827329)
    authdate = db.Column(db.DateTime(), default=datetime(1991,1,1))
    currentlang_code = db.Column(db.String, db.ForeignKey('langs.code'))
    nativelang_code = db.Column(db.String, db.ForeignKey('langs.code'))
    targetlangs = db.relationship('Lang', secondary=user_targetlangs, backref = 'users')
    settings = db.Column(db.String(1000), default='')
    created_on =db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    streakdays = db.Column(db.Integer(), default=0)
    streakdate = db.Column(db.Date(), default=datetime(1991,1,1))
    totalsentences = db.Column(db.Integer(), default=0)
    streakgoal = db.Column(db.Integer(), default=10)
    streaknum = db.Column(db.Integer(), default=0)
    events = db.relationship('Event', backref='user')
    lemmas = db.relationship('Knownlemma', backref='user', cascade='all,delete-orphan')
    known_grammar = db.relationship('Knowngrammar', backref='user') 
    text_record = db.relationship('Textrecord', backref='user') 
    def __repr__(self):
        return "<User:{}:{}>".format(self.id, self.email)


class Lang(db.Model):
    __tablename__ = 'langs'
    code = db.Column(db.String(4), primary_key=True, unique=True)
    #text = db.Column(db.String(15))
    target = db.Column(db.Boolean(), default=False)
    native = db.Column(db.Boolean(), default=False)
    user_currentlang = db.relationship('User', backref = 'currentlang', foreign_keys=[User.currentlang_code])
    user_nativelang = db.relationship('User', backref = 'nativelang', foreign_keys=[User.nativelang_code])
    texts = db.relationship('Text', backref = 'lang')
    lemmas = db.relationship('Lemma', backref='lang')
    grammar = db.relationship('Grammar', backref = 'lang')
    events = db.relationship('Event', backref='lang')
    def __repr__(self):
        return "<Lang:{}>".format(self.code)


links = db.Table('links',
    db.Column('text_id', db.Integer, db.ForeignKey('texts.id'), primary_key=True),
    db.Column('translation_id', db.Integer, db.ForeignKey('texts.id'), primary_key=True))

class Text(db.Model):
    __tablename__ = 'texts'
    id = db.Column(db.Integer(), primary_key=True) # Tatoeba are negative other are positive
    type = db.Column(db.String(255), default='') # Sentence , paragraph, dialog?
    lang_code = db.Column(db.String, db.ForeignKey('langs.code'))
    text = db.Column(db.Text(), default= None, nullable=False)
    audios = db.relationship('Audio', backref='text', cascade='all,delete-orphan')
    tokens = db.relationship('Token', backref='text', cascade='all,delete-orphan')
    json = db.Column(db.Text(), default='')
    model = db.Column(db.String(255), default='')
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    date_last_modified = db.Column(db.DateTime())
    translations = db.relationship('Text', secondary=links, backref='texts', primaryjoin=id ==links.c.text_id, secondaryjoin=id == links.c.translation_id)
    text_record = db.relationship('Textrecord', backref='text') 
    events = db.relationship('Event', backref='text')
    def __repr__(self):
        return "<Text:{}:{}>".format(self.id, self.text)


class Audio(db.Model):
    __tablename__ = 'audios'
    id = db.Column(db.Integer(), primary_key=True) # Tatoeba are negative other are positive
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    username = db.Column(db.String(255))
    license = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return "<Audio:{}:{}>".format(self.id, self.text_id)

'''class Tag(db.Model):
    __tablename__ = 'tags'

    text_id = db.Column(db.Integer(), primary_key=True)
    tag_name = db.Column(db.String(100))'''

'''token_morphs = db.Table('token_morphs',
    db.Column('token_id', db.Integer, db.ForeignKey('tokens.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id'))
    )'''
token_grammar = db.Table('token_grammar',
    db.Column('token_id', db.Integer, db.ForeignKey('tokens.id')),
    db.Column('grammar_id', db.Integer, db.ForeignKey('grammar.id'))
    )

class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer(), primary_key=True)
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    position = db.Column(db.Integer())
    lemma_id = db.Column(db.Integer, db.ForeignKey('lemmas.id')) #TODO many to many or one to one
    #pos_id = db.Column(db.Integer, db.ForeignKey('grammar.id'))
    #tag_id = db.Column(db.Integer, db.ForeignKey('grammar.id'))
    #ent_id = db.Column(db.Integer, db.ForeignKey('grammar.id'))
    def __repr__(self):
        return "<Token:{}:{}>".format(self.id, self.position)

class Lemma(db.Model):
    __tablename__ = 'lemmas'
    id = db.Column(db.Integer(), primary_key=True)
    lang_code = db.Column(db.String, db.ForeignKey('langs.code'))
    lemma = db.Column(db.String(255), nullable=False)
    #count = db.Column(db.Integer(), default=1)
    tokens = db.relationship('Token', backref='lemma')
    info_users = db.relationship('Knownlemma', backref='lemma')
    def __repr__(self):
        return "<Lemma:{}:{}>".format(self.id, self.lemma)

class Grammar(db.Model):
    __tablename__ = 'grammar'
    id = db.Column(db.Integer(), primary_key=True)
    lang_code = db.Column(db.String, db.ForeignKey('langs.code'))
    grammartype = db.Column(db.String(255))
    grammar = db.Column(db.String(255))
    #count = db.Column(db.Integer(), default=1)
    #token_pos = db.relationship('Token', backref = 'pos', foreign_keys=[Token.pos_id])
    #token_tag = db.relationship('Token', backref='tag', foreign_keys=[Token.tag_id])
    #token_ent = db.relationship('Token', backref='ent', foreign_keys=[Token.ent_id])
    #token_morphs = db.relationship('Token', secondary=token_morphs, backref='morphs')
    tokens = db.relationship('Token', secondary=token_grammar, backref='grammar')
    known = db.relationship('Knowngrammar', backref='grammar')
    def __repr__(self):
        return "<Grammar:{}:{}:{}>".format(self.id, self.grammartype, self.grammar)

class Knownlemma(db.Model):
    __tablename__ = 'knownlemma'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    lemma_id = db.Column(db.Integer(), db.ForeignKey('lemmas.id'))
    count = db.Column(db.Integer(), default=0) #TODO this could be done to events when sentencs are done
    date = db.Column(db.Date(), default=datetime(1991,1,1), onupdate=datetime.utcnow) #TODO this could be done to events when sentencs are done
    def __repr__(self):
        return "<Known Lemma:{}:{}:{}>".format(self.user_id, self.lemma_id, self.count)

class Textrecord(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    text_id = db.Column(db.Integer(), db.ForeignKey('texts.id'))
    count = db.Column(db.Integer(), default=0) #TODO this could be done to events when sentencs are done
    date = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow) #TODO this could be done to events when sentencs are done

class Knowngrammar(db.Model):
    id = db.Column(db.Integer(), primary_key=True, )
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    grammar_id = db.Column(db.Integer(), db.ForeignKey('grammar.id'))
    count = db.Column(db.Integer(), default=0) #TODO this could be done to events when sentencs are done
    date = db.Column(db.Date(), default=datetime(1991,1,1), onupdate=datetime.utcnow) #TODO this could be done to events when sentencs are done
    unknown = db.Column(db.Boolean())
    known = db.Column(db.Boolean())
    focus = db.Column(db.Boolean())

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer(), primary_key=True)
    date_time = db.Column(db.DateTime(), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lang_code = db.Column(db.Integer, db.ForeignKey('langs.code'))
    text_id = db.Column(db.Integer, db.ForeignKey('texts.id'))
    event_type = db.Column(db.String(255), default='')
    event_info = db.Column(db.Text())
    def __repr__(self):
        return "<Event:{}:{}:{}>".format(self.id, self.date_time, self.event_type)
