from flask import Blueprint, current_app
from . import db, parser
from tatoebatools import tatoeba
from .models import User, Lang, Text, Audio, Lemma, Grammar, Token, Event
import time, json

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
				new.targets.append(lang)
			if  not test.target == config['TARGET_LANG'][lang]:
				test.target = config['TARGET_LANG'][lang]
				new.natives.append(lang)
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
			test = Audio.query.filter(Audio.id == -1*a.audio_id).first()
			if test:
				if test.text_id != -1*a.sentence_id:
					test.text_id = -1*a.sentence_id
			else:
				db.session.add(Audio(id=-1*a.audio_id, text_id=-1*a.sentence_id, license=a.license, username=a.username))
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
				if sub =='pos':
					newtoken.pos = sqlgrammar
				elif sub =='ent':
					newtoken.ent = sqlgrammar
				elif sub =='tag':
					newtoken.tag = sqlgrammar
				else:
					newtoken.morphs.append(sqlgrammar)

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

def pullusergrammar(lang, user):
	db = f'{lang}_tag'
	if (not touchuserdb(lang, user, db)):
		createusergrammar(lang, user)
	pur, pon = userdatabase(user)
	grammar = {}
	subs = ['tag', 'ent_type', 'POS']
	for row in pur.execute(f"SELECT morph FROM {lang}_morphs").fetchall():
		subs.append(sqlsafe(row['morph']))

	for sub in subs:
		grammar[sub] = {}
		for each in pur.execute(f"SELECT {sub}, unknown, known, focus FROM {lang}_{sub}").fetchall():
			grammar[sub][each[sub]] = {'unknown':each['unknown'], 'known':each['known'], 'focus':each['focus']}

	pon.commit()
	pon.close()
	return grammar