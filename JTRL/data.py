from flask import Blueprint, current_app
from . import db, parser
from tatoebatools import tatoeba
from datetime import datetime, timedelta
from .models import User, Lang, Text, Audio, Lemma, Grammar, Token, Event, Knowngrammar, Knownlemma, Textrecord
import time, json, jaconv, os, wget
from sqlalchemy import select, or_, and_, exists

config = current_app.config
logger = current_app.logger
parser = parser.parser(config['SPACY_MODELS'][config['SPACY_MODEL']])
config['NATIVE_SET'] = set()
config['TARGET_SET'] = set()
for lang in config['NATIVE_LANG']:
	if config['NATIVE_LANG'][lang]:
		config['NATIVE_SET'].add(lang)
for lang in config['TARGET_LANG']:
	if config['TARGET_LANG'][lang]:
		config['TARGET_SET'].add(lang)

data = Blueprint('data', __name__)

def database():
	db.create_all()
	if config['SKIP_BUILD']:
		return
	if (config['FORCE_REBUILD']):
		test = input("Config file is set to force rebuilt. Are you sure you want to contiune? (Y/N):")
		test = test.upper()
		if (test != "Y" and test != "YES"):
			config['FORCE_REBUILD'] = False

	if config['FORCE_REBUILD']:
		config['FORCE_REBUILD'] = False
		db.drop_all()
		db.create_all()
		logger.info('Database cleared')

	new = addlangs()
	# This adds text audio and translations for sentences not in the database before
	for lang in new['new']:
		addtext(lang)
	for lang in new['targets']:
		addaudio(lang)
		parsetext(lang)
		addtranslations(lang, config['NATIVE_SET'])
	for lang in config['TARGET_SET'].difference(new['targets']):
		addtranslations(lang, new['natives'])

	# if the language is already loaded, either addes just new sentences if complete or all if partially loaded
	for lang in config['NATIVE_SET'].union(config['TARGET_SET']).difference(new['new']):
		scope = 'added'
		if Text.query.filter(Text.lang_code == lang).count() <= config['TESTING_MAX']:
			scope = 'all'
		addtext(lang, scope)
	for lang in config['TARGET_SET'].difference(new['targets']):
		scope = 'added'
		if Text.query.filter(Text.lang_code == lang).count() <= config['TESTING_MAX']:
			scope = 'all'
		addaudio(lang, scope)
		parsetext(lang, scope)
		addtranslations(lang, config['NATIVE_SET'], scope)
	#TODO Add REMOVE section, add remove cascade from models.py


def addlangs():
	new = {'targets':set(), 'natives':set(), 'new':set()}
	for lang in config['NATIVE_LANG']: #tatoeba.all_languages:
		test = Lang.query.filter(Lang.code == lang).first()
		if test:
			if not test.native == config['NATIVE_LANG'][lang]:
				test.native = config['NATIVE_LANG'][lang]
				new['targets'].add(lang)
			if  not test.target == config['TARGET_LANG'][lang]:
				test.target = config['TARGET_LANG'][lang]
				new['natives'].add(lang)
		else:
			db.session.add(Lang(code=lang, native=config['NATIVE_LANG'][lang], target=config['TARGET_LANG'][lang]))
			if lang in config['NATIVE_SET']:
				new['natives'].add(lang)
				new['new'].add(lang)
			if lang in config['TARGET_SET']:
				new['targets'].add(lang)
				new['new'].add(lang)

	logger.info(f"Lang table rebuilt")
	db.session.commit()
	return new

def addtext(lang, scope="all"):#TODO need to have initial creatation vs update)
	logger.info(f"Rebuilding {lang} database.")
	starttime = time.time()
	i = 0
	for s in tatoeba.sentences_detailed(lang, scope=scope): # Limit by language to increase build speed and possibly query speed?
		test = Text.query.filter(Text.id == -1*s.sentence_id).first()
		if test:
			if s.text != test.text:
				test.text = s.text
				test.date_last_modified=s.date_last_modified
				#TODO Keep track to update grammar and lemma
		else:
			db.session.add(Text(id = -1*s.sentence_id, lang=Lang.query.filter_by(code=s.lang).first(), type='sentence', text=s.text, date_last_modified=s.date_last_modified))
		i += 1
		if i%config['TABLE_CHUNK'] == 0:
			db.session.commit()
			logger.info(f"{i} sentences added or checked in {lang}")
		if i == config['TESTING_CHUNK']:
			break

	logger.info(f"It took {(time.time()-starttime)/60} minutes to add {lang} to Text table")
	db.session.commit()

def addaudio(lang, scope="all"):
	logger.info(f"Adding {lang} to Audio table.")
	starttime = time.time()
	i = 0
	for a in tatoeba.sentences_with_audio(lang, scope=scope):
		if a.license:
			test = Audio.query.filter(Audio.id == a.audio_id).first()
			if test:
				if test.text_id != -1*a.sentence_id:
					test.text_id = -1*a.sentence_id
			else:
				db.session.add(Audio(id=a.audio_id, text_id=-1*a.sentence_id, license=a.license, username=a.username))
		i += 1
		if i%config['TABLE_CHUNK'] == 0:
			db.session.commit()
			logger.info(f"{i} audio added or checked in {lang}")
		if i == config['TESTING_CHUNK']:
			break

	logger.info(f"It took {(time.time()-starttime)/60} minutes to add {lang} to Audio table")
	db.session.commit()

def addtranslations(lang, langs, scope="all"):
	logger.info(f"Adding {lang} to Links Table.")
	starttime = time.time()
	for nlang in langs:
		if lang == nlang:
			continue
		i = 0
		for t in tatoeba.links(lang, nlang, scope=scope):
			s = Text.query.filter(Text.id == -1*t.sentence_id).first()
			x = Text.query.filter(Text.id == -1*t.translation_id).first()
			if x and s:
				if not x.id in s.translations:
					s.translations.append(x)
			i += 1
			if i%config['TABLE_CHUNK'] == 0:
				db.session.commit()
				logger.info(f"{i} translations added or check from {lang} to {nlang}")
			if i == config['TESTING_CHUNK']:
				break

	logger.info(f"It took {(time.time()-starttime)/60} minutes to add {lang} to links table")
	db.session.commit()

def parsetext(lang, scope='all'):
	logger.info(f"Adding {lang} parsing to json in text table.")
	starttime = time.time()
	i = 0
	#sqllang = Lang.query.filter(Lang.code == lang).first()
	for row in Text.query.filter(Text.lang_code == lang, Text.model != config['SPACY_MODEL']).all():
		parsed =parser.parse(row.text, lang)
		tokens =[]
		for i, token in enumerate(parsed): 
			lemma = token.lemma_.lower().strip()
			morphs =token.morph.to_dict()
			bit = {'text':token.text, 'lemma':lemma, 'vocab':parser.vocab(token.lemma, lang), 'isoov':token.is_oov, 'pos':token.pos_, 'ent':token.ent_type_, 'tag':token.tag_, **morphs}
			tokens.append(bit)
			#if not bit['vocab']:
			#	continue
			newtoken = Token(text=row, position=i)
			sqllemma = Lemma.query.filter(Lemma.lemma == lemma, Lemma.lang_code == lang).first()
			if not sqllemma: 
				sqllemma = Lemma(lang_code=lang, lemma=lemma)
				db.session.add(sqllemma)
			newtoken.lemma = sqllemma
			subs = list(morphs.keys()) + ['pos', 'ent', 'tag']
			for sub in subs:
				if sub == 'Reading' or (sub =='ent' and bit[sub]==''):
					continue
				sqlgrammar = Grammar.query.filter(Grammar.lang_code == lang, Grammar.grammartype == sub, Grammar.grammar == bit[sub]).first()
				if not sqlgrammar:
					sqlgrammar = Grammar(lang_code=lang, grammar=bit[sub], grammartype=sub)
					db.session.add(sqlgrammar)
				newtoken.grammar.append(sqlgrammar)	
				'''if sub =='pos':
					newtoken.pos = sqlgrammar
				elif sub =='ent':
					newtoken.ent = sqlgrammar
				elif sub =='tag':
					newtoken.tag = sqlgrammar
				else:
					newtoken.morphs.append(sqlgrammar)'''

			db.session.add(newtoken)
		row.json = json.dumps(tokens, ensure_ascii=False).encode('utf8')
		row.model = config['SPACY_MODEL']
		i += 1
		if i%config['TABLE_CHUNK'] == 0:
			db.session.commit()
			logger.info(f"{i} paresed or checked in {lang}")
		if i == config['TESTING_CHUNK']:
			break

	logger.info(f"It took {(time.time()-starttime)/60} minutes to add {lang} parsing to json in text table")
	db.session.commit()

def pullusergrammar(user):
	grammar = {}
	allgram = Grammar.query.filter(Grammar.lang_code == user.currentlang_code).all()
	for gram in Knowngrammar.query.filter(Knowngrammar.user_id == user.id).all():
		if gram.grammar.lang_code != user.currentlang_code:
			continue
		if not gram.grammar.grammartype in grammar:
			grammar[gram.grammar.grammartype] = {}
		grammar[gram.grammar.grammartype][gram.grammar.grammar] = {'unknown':gram.unknown, 'known':gram.known, 'focus':gram.focus}
		allgram.remove(gram.grammar)
	for gram in  allgram:
		if not gram.grammartype in grammar:
			grammar[gram.grammartype] = {}
		grammar[gram.grammartype][gram.grammar] = {'unknown': 0, 'known':1, 'focus':0}
		if gram.grammartype == 'pos' and (gram.grammar == 'NUM' or gram.grammar == 'PUNCT'):
			grammar[gram.grammartype][gram.grammar]['unknown'] = 1

	return grammar

def pushusergrammar(user, grammar):
	allgram = Grammar.query.filter(Grammar.lang_code == user.currentlang_code).all()
	for gram in Knowngrammar.query.filter(Knowngrammar.user_id == user.id).all():
		if gram.grammar.lang_code != user.currentlang_code:
			continue
		if not gram.grammar.grammartype in grammar:
			allgram.remove(gram.grammar)
			continue
		if not gram.grammar.grammar in grammar[gram.grammar.grammartype]:
			allgram.remove(gram.grammar)
			continue
		gram.unknown = grammar[gram.grammar.grammartype][gram.grammar.grammar]['unknown']
		gram.known = grammar[gram.grammar.grammartype][gram.grammar.grammar]['known']
		gram.focus = grammar[gram.grammar.grammartype][gram.grammar.grammar]['focus']
		allgram.remove(gram.grammar)
	for gram in allgram:
		newknown = Knowngrammar(user_id = user.id, grammar_id=gram.id, unknown=grammar[gram.grammartype][gram.grammar]['unknown'],
			known =grammar[gram.grammartype][gram.grammar]['known'], focus=grammar[gram.grammartype][gram.grammar]['focus'])
		db.session.add(newknown)
	db.session.commit()

def addlemmagrammar(words, user):
	parsed = parser.parse(words, user.currentlang_code)
	grammar = {'tag':{}, 'pos':{}, 'ent':{}}
	lemmas = set()
	usergrammar = pullusergrammar(user)
	for token in parsed:
		lemma = token.lemma_.lower().strip()
		lemmas.add(lemma)

		tokendict = token.morph.to_dict()
		for morph in tokendict:
			if (morph != 'Reading'):
				if (not morph in grammar):
					grammar[morph] = {}
				if (not tokendict[morph] in grammar[morph] and tokendict[morph] in usergrammar[morph]):
					grammar[morph][tokendict[morph]] = {'unknown': usergrammar[morph][tokendict[morph]]['unknown'], 'known': 1, 'focus': usergrammar[morph][tokendict[morph]]['focus']}
		if (not token.tag_ in grammar['tag'] and token.tag_ in usergrammar['tag']):
			grammar['tag'][token.tag_] = {'unknown': usergrammar['tag'][token.tag_]['unknown'], 'known': 1, 'focus': usergrammar['tag'][token.tag_]['focus']}
		if (not token.pos_ in grammar['pos'])and token.pos_ in usergrammar['pos']:
			grammar['pos'][token.pos_] = {'unknown': usergrammar['pos'][token.pos_]['unknown'], 'known': 1, 'focus': usergrammar['pos'][token.pos_]['focus']}
		if (not token.ent_type_ in grammar['ent'] and token.ent_type_ in usergrammar['ent']):
			grammar['ent'][token.ent_type_] = {'unknown': usergrammar['ent'][token.ent_type_]['unknown'], 'known': 1, 'focus': usergrammar['ent'][token.ent_type_]['focus']}

	#TODO need to filter non lemma and knownlemma using sql
	lemmas2 = set()
	test = Lemma.query.filter(Lemma.lang_code == user.currentlang_code).all()
	for lemma in test:
		if (lemma.lemma in lemmas):
			lemmas2.add(lemma)
			lemmas.remove(lemma.lemma)

	
	test = Knownlemma.query.filter(Knownlemma.user_id == user.id).all()
	for known in test:
		if (known.lemma in lemmas2):
			lemmas2.remove(known.lemma)

	for lemma in lemmas2:
		newknown = Knownlemma(user_id = user.id, lemma=lemma)
		db.session.add(newknown)
	db.session.commit()
	return lemmas2, grammar, lemmas

def getknownlemma(user):
	return db.session.query(Knownlemma).join(Lemma).filter(Knownlemma.user == user, Lemma.lang == user.currentlang).all()

def additionalinfo(text): 
	info = None
	if (text.lang_code == 'jpn'):
		tokens = json.loads(text.json)
		reading = ""
		for token in tokens:
			if ('Reading' in token and token['text'] != '？'):
				reading += '  ' + token['Reading']
			if token['text'] == '？':
				reading += '?'
		info = jaconv.kata2hira(reading)
	return info

def getaudiofiles(text):
	files = [] #TODO pass username and license and add computer generated sound files 
	for audioid in text.audios:
		filename = str(-1*text.id) + '-' + str(audioid.id) + '.mp3'
		filepath = './JTRL/static/audio/' + filename
		if (not os.path.isfile(filepath)):
			wget.download(f"https://tatoeba.org/audio/download/{audioid.id}", './JTRL/static/audio/')
			logger.info(f'Audio file for {audioid.id} Downloaded')
		else:
			logger.info(f'Audio file for {filename} already downloaded')
		files.append(filename)
	return files

def nexttext(user):
	#TODO Need to add grammar to this
	x = 3
	days = datetime.now() - timedelta(days=x)
	print(days)
	lemmaquery = (
		db.session.query(Knownlemma.id)
		.filter(Knowngrammar.user == user, Knownlemma.date < days).exists()
		)
	grammarquery = (
		db.session.query(Grammar.id)
		.join(Knowngrammar)
		.filter(Knowngrammar.user == user, Knowngrammar.known)
		)

	subquery = (
		db.session
		.query(Token.id)
		.join(Lemma, Token.lemma)
		.outerjoin(Knownlemma)
		.join(Grammar, Token.grammar)
		.outerjoin(Knowngrammar)
		.filter(or_(and_(Knownlemma.user == user, ~Token.grammar.any(Grammar.id.notin_(grammarquery))), Knowngrammar.unknown))	
		.distinct(Token.id)
		)

	query = (
		db.session
		.query(Text)
		.join(Token).join(Lemma).outerjoin(Knownlemma)
		.outerjoin(Textrecord).order_by(Textrecord.date.asc(), db.case([(lemmaquery, Knownlemma.date)], else_=datetime.max))
		.filter(~Text.tokens.any(Token.id.notin_(subquery)), Text.lang == user.currentlang)
		)
	text = query.first()
	test = query.all()
	print(len(test))
	print(test)

	return text

def recordtext(user, textid):
	knowns  = Knowngrammar.query.filter(Knowngrammar.user == user).join(Grammar).join(Token, Grammar.tokens).join(Text).filter(Text.id == textid).all()
	for known in knowns:
		known.count += 1
	lemmas = Knownlemma.query.filter(Knownlemma.user == user).join(Lemma).join(Token, Lemma.tokens).join(Text).filter(Text.id == textid).all()
	for lemma in lemmas:
		lemma.count += 1
	record = Textrecord.query.filter(Textrecord.text_id == textid, Textrecord.user == user).first()
	if record == None:
		db.session.add(Textrecord(user=user, text_id=textid, count=1))
	else:
		record.count += 1

	db.session.commit()