from deep_translator import GoogleTranslator as gt
from random import randrange
import vlc
import parser
import sqlite3
import datetime
import wget
import os
import bz2
import time
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if __name__ == '__main__':
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	if (not os.path.exists('./logs/')):
		os.mkdir('./logs/')
	fh = logging.FileHandler('./logs/database.log')
	fh.setLevel(logging.DEBUG)
	fh.setFormatter(formatter)
	logger.addHandler(fh)


gtd = {'cat': 'ca', 'cmn': 'zh-CN', #traditional chinese 'cmn': 'zh-TW', 
	'hrv': 'hr', 'dan': 'da', 'nld': 'nl', 'eng': 'en', 'fin': 'fi', 'fra': 'fr',
	'deu': 'de', 'ell': 'el', 'ita': 'it', 'jpn': 'ja', 'kor': 'ko',
	'lit': 'lt', 'mkd': 'mk', 'nob': 'no', 'pol': 'pl', 'por': 'pt', 
	'ron': 'ro', 'rus': 'ru', 'spa': 'es', 'swe': 'sv', 'ukr': 'uk'}

codetoname = {'cat': 'Catalan', 'cmn': 'Chinese (simplified)', 'hrv': 'Croatian', 'dan':'Danish',
	'nld': 'Dutch', 'eng': 'English', 'fin': 'Finnish', 'fra': 'French',
	'deu': 'German', 'ell': 'Greek', 'ita': 'Italian', 'jpn': 'Japanese', 'kor': 'Korean',
	'lit': 'Lithuanian', 'mkd':'Macedonian', 'nob': 'Norwegian', 'pol': 'Polish', 'por': 'Portuguese', 
	'ron': 'Romanian', 'rus': 'Russian', 'spa': 'Spanish', 'swe': 'Swedish', 'ukr': 'Ukrainian'}
path = './tatoeba/'
http = 'https://downloads.tatoeba.org/exports/'

mode = 'json' # 'brute' 'sql'
passgrammar = ['NUM', 'PUNCT', 'SYM', 'X']

def test():
	pass
	#print(gt().get_supported_languages(as_dict=True))

def database(): 
	don = sqlite3.connect("database.db")
	don.row_factory = sqlite3.Row
	dur = lon.cursor()
	logger.info('Connected to main Database.')
	return dur, don

def langdatabase(lang): 
	if (not os.path.exists('./lang/')):
		os.mkdir('./lang/')
	con = sqlite3.connect(f"./lang/{lang}.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	logger.info(f'Connected to {lang} Database.')
	return cur, con

def userdatabase(user): 
	if (not os.path.exists('./user/')):
		os.mkdir('./user/')
	pon=sqlite3.connect(f"./user/{user}.db")
	pon.row_factory = sqlite3.Row
	logger.info(f"Connected to {user}'s Database")
	return pon.cursor(), pon

def addlemma(words, lang, user):
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_known_lemma'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_known_lemma(lemma, count, date)")
	parsed =parser.parse(words, lang)
	lemmas = []
	for token in parsed:
		if (not token.lemma_ in lemmas and not token.pos_ == "PUNCT"):
			lemmas.append(token.lemma_)

	test = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	for lemma in test:
		if (lemma[0] in lemmas):
			lemmas.remove(lemma[0])

	pur.executemany(f"INSERT INTO {lang}_known_lemma VALUES (?, ?, ?)",[(lemma, 0, '1991-01-01') for lemma in lemmas])
	logger.info(f"New lemma inserted into {user}'s database:{lemmas}")
	pon.commit()
	pon.close()
	return lemmas

def updatelemma(lemma, lang, user): #TODO what if lemma not in Database?
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT count FROM {lang}_known_lemma WHERE lemma = '{lemma}'").fetchone()
	pur.execute(f"UPDATE {lang}_known_lemma SET date = ?, count = ? WHERE lemma = ?",(datetime.date.today(), count['count']+1, lemma))
	logger.info(f'Lemma, {lemma}, updated for {user}')
	pon.commit()
	pon.close()

def updatesentencelemma(num, lang, user):
	cur, con = langdatabase(lang)
	print(lang, num)
	blob = json.loads(cur.execute(f"SELECT id, json FROM {lang}_json WHERE id = {str(num)}").fetchone()['json'])
	for each in blob:
		if (not each['POS'] in passgrammar):
			updatelemma(each["lemma"], lang, user)
	con.close()

def removelemma(words, lang, user):
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_known_lemma'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_known_lemma(lemma, count, date)")
	parsed =parser.parse(words, lang)
	lemmas = []
	for token in parsed:
		if (not token.lemma_ in lemmas):
			lemmas.append(token.lemma_)

	test = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	for thing in test:
		if (thing['lemma'] in lemmas):
			pur.execute(f"DELETE FROM {lang}_known_lemma WHERE lemma = ?", thing)
			logger.info(f"{thing['lemma']} removed from {user}'s Database")

	pon.commit()
	pon.close()

def getoldestlemma(lang, user, count):
	pur, pon = userdatabase(user)
	oldestlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma ORDER BY date LIMIT ?",(count,)).fetchall()
	pon.close()
	logger.info(f"Current oldest lemma for {user} is {oldestlemma}")
	return oldestlemma

def getlemmainfo(word, lang, user):
	pur, pon = userdatabase(user)
	parsed = parser.parse(word, lang)
	info = pur.execute(f"SELECT lemma, count, date FROM {lang}_known_lemma WHERE lemma = ?",(parsed[0].lemma_,)).fetchone()
	pon.close()
	logger.info(f"{info} found for {user}'s word: {word}")
	return info

def loadlang(lang):
	cur, con = langdatabase(lang)
	filename =f"{lang}_sentences.tsv.bz2"

	if (not os.path.exists(path)):
		os.mkdir(path)

	if (os.path.isfile(path + filename)):
		if (time.time()-os.path.getmtime(f"{path}{filename}")>604800):
			os.remove(path + filename)
			wget.download(f"{http}per_language/{lang}/{filename}", path)
	else:
		wget.download(f"{http}per_language/{lang}/{filename}", path)

	file = bz2.open(f"{path}{filename}", "r")

	cur.execute(f"DROP TABLE IF EXISTS {lang}")
	cur.execute(f"CREATE TABLE {lang}('id' INTEGER PRIMARY KEY, lang, text) WITHOUT ROWID")

	for line in file:
		line = str(line[:-1],'UTF-8').split("\t")
		cur.execute(f"INSERT INTO {lang} VALUES (?,?,?)",line)
	logger.info(f"{lang} database for language, {lang} has been updated")
	con.commit()
	con.close()

def loadaux(aux):
	lur, lon = langdatabase('all_lang')
	filename =f"{aux}.tar.bz2"

	if (os.path.isfile(path + filename)):
		if (time.time()-os.path.getmtime(f"{path}{filename}")>604800):
			os.remove(path + filename)
			wget.download(f"{http}{filename}", path)
	else:
		wget.download(f"{http}{filename}", path)

	file = bz2.open(f"{path}{filename}", "r")

	lur.execute(f"DROP TABLE IF EXISTS {aux}")
	lur.execute(f"CREATE TABLE {aux}(id, data)")

	for line in file:
		try:
			line = str(line[:-1],'UTF-8').split("\t")[:2]
			lur.execute(f"INSERT INTO {aux} VALUES (?,?)",line)
		except:
			pass
	logger.info(f'all_lang database {aux} rebuilt')
	lon.commit()
	lon.close()

'''def processsentencesraw(lang, user):#TODO refine grammar filter after grammar is refined
	t = time.time()
	cur, con = langdatabase(lang)
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_available_sentences'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_available_sentences(id, count, date)")

	pur.execute(f"DROP TABLE IF EXISTS {lang}_close_lemma")
	pur.execute(f"CREATE TABLE {lang}_close_lemma(lemma, count)")

	knownlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	if (len(knownlemma)==0):
		return
	passgrammar = ['NUM', 'PUNCT', 'SYM', 'X']

	parsertime = 0
	for row in cur.execute(f"SELECT id, text FROM {lang}").fetchall(): 
		pt = time.time()
		parsed =parser.parse(row['text'], lang)
		parsertime = parsertime + time.time() - pt
		missing = []
		#tokens = []   #TODO pretty sure this is not used

		for token in parsed:

			if (not(token.pos_ in passgrammar or (token.lemma_,) in knownlemma)):
				missing.append(token.lemma_)
			if (len(missing) == 2):
				break

		if (len(missing) == 0):
			if not row['id'] in pur.execute(f"SELECT id FROM {lang}_available_sentences").fetchall():
				pur.execute(f"INSERT INTO {lang}_available_sentences VALUES (?, ?, ?)",(row['id'], 0, '1991-01-01'))
			logger.info(f"Sentence {row['id']} added to available sentences in {lang} for {user}")
		elif (len(missing) == 1):
			if (missing[0],) in pur.execute(f"SELECT lemma FROM {lang}_close_lemma").fetchall():
				count = pur.execute(f"SELECT count FROM '{lang}_close_lemma' WHERE lemma = ?",(missing[0],)).fetchone()
				pur.execute(f"UPDATE {lang}_close_lemma SET count = ? WHERE lemma = ?",(count[0] + 1, missing[0]))
			else:
				pur.execute(f"INSERT INTO {lang}_close_lemma VALUES (?,?)",(missing[0], 1))
	con.commit()
	con.close()
	pon.commit()
	pon.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed sentences in {lang} for {user}")
	parsertime = parsertime/60
	logger.info(f'Language parsing took {parsertime} mintues')'''

def processlangjson(lang): #Reduce to only needed grammar once grammar refinded
	t = time.time()
	cur, con = langdatabase(lang)
	cur.execute(f"DROP TABLE IF EXISTS {lang}_json")
	cur.execute(f"CREATE TABLE {lang}_json(id, json)")
	for row in cur.execute(f"SELECT id, text FROM {lang}").fetchall(): 
		parsed =parser.parse(row['text'], lang)
		tokens =[]
		for token in parsed:
			bit = {'text':token.text, 'lemma':token.lemma_, 'POS':token.pos_, 'ent_type':token.ent_type_, 'tag':token.tag_, 'morph':token.morph.to_dict()}
			tokens.append(bit)
		cur.execute(f"INSERT INTO {lang}_json VALUES (?,?)",(row['id'], json.dumps(tokens)))
	con.commit()
	con.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed sentences to json in {lang}")
	logger.info(f"{lang} processed to SQL with Json lemma and Grammar")

def processsentencesjson(lang, user): #refine pass grammar, tags grammar and out of language words
	t = time.time()
	cur, con = langdatabase(lang)
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_available_sentences'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_available_sentences(id, count, date)")

	pur.execute(f"DROP TABLE IF EXISTS {lang}_close_lemma")
	pur.execute(f"CREATE TABLE {lang}_close_lemma(lemma, count)")

	knownlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	if (len(knownlemma)==0):
		return
	parsertime = 0
	
	knownlemma = [lemma['lemma']for lemma in knownlemma]
	for row in cur.execute(f"SELECT id, json FROM {lang}_json").fetchall(): 
		pt = time.time()
		parsed = json.loads(row['json'])
		parsertime = parsertime + time.time() - pt
		missing = []

		for token in parsed:
			if (not(token['POS'] in passgrammar or token['lemma'] in knownlemma)):
				missing.append(token['lemma'])
			if (len(missing) == 2):
				break

		if (len(missing) == 0):
			if not row['id'] in pur.execute(f"SELECT id FROM {lang}_available_sentences").fetchall():
				pur.execute(f"INSERT INTO {lang}_available_sentences VALUES (?, ?, ?)",(row['id'], 0, '1991-01-01'))
			logger.info(f"Sentence {row['id']} added to available sentences in {lang} for {user}")
		elif (len(missing) == 1):
			if (missing[0],) in pur.execute(f"SELECT lemma FROM {lang}_close_lemma").fetchall():
				count = pur.execute(f"SELECT count FROM '{lang}_close_lemma' WHERE lemma = ?",(missing[0],)).fetchone()
				pur.execute(f"UPDATE {lang}_close_lemma SET count = ? WHERE lemma = ?",(count['count'] + 1, missing[0]))
			else:
				pur.execute(f"INSERT INTO {lang}_close_lemma VALUES (?,?)",(missing[0], 1))
	con.commit()
	con.close()
	pon.commit()
	pon.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed sentences from json in {lang} for {user}")
	parsertime = parsertime/60
	logger.info(f'Language json retrival took {parsertime} mintues')

'''def processlangsql(lang): #Refine Grammar
	cur, con = langdatabase(lang)
	cur.execute(f"DROP TABLE IF EXISTS {lang}_sql_lemma")
	cur.execute(f"CREATE TABLE {lang}_sql_lemma(lemma, id)")
	cur.execute(f"DROP TABLE IF EXISTS {lang}_sql_grammar")
	cur.execute(f"CREATE TABLE {lang}_sql_grammar(grammar, id)")

	con.commit()
	con.close()
	logger.info(f"{lang} processed to SQL with an entry for each lemma and Grammar")'''


def pickrandomsentence(lang, user):
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT COUNT(*) FROM {lang}_available_sentences").fetchone()[0]
	print(count)
	sentence = pur.execute(f"SELECT id FROM {lang}_available_sentences WHERE rowid = ?",(randrange(count),)).fetchone()['id']
	pon.close()
	logger.info(f'Random sentence {sentence} picked for {user}')
	return sentence

def picknextsentence(lang, user): 
	pur, pon = userdatabase(user)
	sentence =  pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchone()['id']
	pon.close()
	logger.info(f'The next sentence, {sentence} picked for {user}')
	return sentence

def pickoldestlemmasentence(lang, user):# add option to pull from json or sql
	pur, pon = userdatabase(user)
	old = getoldestlemma(lang, user, 1)
	bank = pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchall()
	for row in bank:
		text = cur.execute(f"SELECT text FROM {lang} WHERE id = ?", row).fetchone()
		parsed = parser.parse(text['text'], lang)
		for token in parsed:
			if ((token.lemma_,) == old[0]):
				pon.close()
				logger.info(f'Picked the sentence {row} for the lemma {old} for {user}')
				return row[0]
	pon.close()
	logger.info(f'Could not find a sentence with the lemma {old} for {user}')

def gettext(num, lang):
	logger.warning('getting text')
	cur, con = langdatabase(lang)
	text = cur.execute(f"SELECT text FROM {lang} WHERE id = ?", (num,)).fetchone()['text']
	con.close()
	logger.info(f'Returning {text} from sentence {num}')
	return text

def marksentence(num, lang, user):
	pur, pon = userdatabase(user)
	print(num)
	count = pur.execute(f"SELECT count FROM '{lang}_available_sentences' WHERE id = {str(num)}").fetchone()
	print(count)
	pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = ? WHERE id = ?",(datetime.date.today(), count['count'] + 1, num))
	pon.commit()
	pon.close()
	logger.info(f'Marking sentence, {num} as read by {user}')

def getgoogle(num, targetlang, nativelang): 
	cur, con = langdatabase(targetlang)
	info = cur.execute(f"SELECT text FROM {targetlang} WHERE id = {num}").fetchone()
	con.close()
	translation = gt(source=gtd[targetlang], target=gtd[nativelang]).translate(info['text'])
	logger.info(f'Returning google translation for sentence, {num} in {nativelang}')
	return translation

def gettranslations(num, lang): #TODO test
	lur, lon = langdatabase('all_lang')
	cur, con = langdatabase(lang)
	ids = lur.execute(f"SELECT data FROM links WHERE id = '{num}'").fetchall()
	translations = cur.execute(f"SELECT text FROM {lang} WHERE id IN '{ids}'").fetchall()
	con.close()
	lon.close()
	logger.info(f'Returning database translations for sentence {num} in {lang}')
	return translations

def getaudioids(num):
	lur, lon = langdatabase('all_lang')
	ids = lur.execute(f"SELECT data FROM sentences_with_audio WHERE id = '{num}'").fetchall()
	lon.close()
	logger.info(f'Returning audio ids for sentence {num}: {ids}')
	return ids

def getaudiofile(audioid):
	lur, lon = langdatabase('all_lang')
	if (not os.path.exists('./static/')):
		os.mkdir('./static/')
	if (not os.path.exists('./static/audio/')):
		os.mkdir('./static/audio')
	num = lur.execute(f"SELECT id FROM sentences_with_audio WHERE data = ?", audioid).fetchone()['id']
	filename = num + '-' + audioid[0] + '.mp3'
	filepath = './static/audio/' + filename
	if (not os.path.isfile(filepath)):
		wget.download(f"https://tatoeba.org/audio/download/{audioid[0]}", './static/audio/')
		logger.info(f'Audio file for {audioid} Downloaded')
	else:
		logger.info(f'Audio file for {audioid[0]} already downloaded')
	lon.close()
	return filename

def getaudiofiles(audioids):
	files = []
	for audioid in audioids:
		files.append(getaudiofile(audioid))
	return files

'''def playaudio(filename): #TODO Currently direcly plays the audio but needs a sleep. 
	#Needs to be in a loop to remove sleep or move the playing of the file to html or javascript when thats setup
	p = vlc.MediaPlayer(filename)
	p.play()
	logger.info(f'Playing audio file {filename}')
	time.sleep(1)
	while (p.is_playing()):
		time.sleep(1)'''

def gettags(num):
	lur, lon = langdatabase('all_lang')
	tags = lur.execute(f"SELECT data FROM tags WHERE id = '{num}'").fetchall()
	lon.close()
	logger.info(f'Tags for sentence {num} are {tags}')
	return tags


if __name__ == '__main__' :
	#Testing stuff
	nativelang = 'eng'
	targetlang = 'jpn'
	user = 4
	logger.info(f'database.py run as main')
	test = ["私は眠らなければなりません。", "きみにちょっとしたものをもってきたよ。", "何かしてみましょう。", "何してるの？", "今日は６月１８日で、ムーリエルの誕生日です！"]
	#for words in test:
	#	addlemma(words, targetlang, user)
	#updatesentencelemma(1297, targetlang, user)
	#test()
	processsentencesjson(targetlang, user)
	#processsentencesraw(targetlang, user)
	#updatelemma("は", targetlang, user)
