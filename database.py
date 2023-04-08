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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if __name__ == '__main__':
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	fh = logging.FileHandler('database.log')
	fh.setLevel(logging.DEBUG)
	fh.setFormatter(formatter)
	logger.addHandler(fh)


gtd = {'jpn':'ja', 'eng':'en'}#TODO finish all usable languages
gtd2 = {'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 
	'armenian': 'hy', 'assamese': 'as', 'aymara': 'ay', 'azerbaijani': 'az', 'bambara': 'bm', 
	'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 'bhojpuri': 'bho', 'bosnian': 'bs', 
	'bulgarian': 'bg', 'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 
	'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW', 'corsican': 'co', 
	'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dhivehi': 'dv', 'dogri': 'doi', 
	'dutch': 'nl', 'english': 'en', 'esperanto': 'eo', 'estonian': 'et', 'ewe': 'ee', 
	'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'frisian': 'fy', 'galician': 'gl', 
	'georgian': 'ka', 'german': 'de', 'greek': 'el', 'guarani': 'gn', 'gujarati': 'gu', 
	'haitian creole': 'ht', 'hausa': 'ha', 'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 
	'hmong': 'hmn', 'hungarian': 'hu', 'icelandic': 'is', 'igbo': 'ig', 'ilocano': 'ilo', 
	'indonesian': 'id', 'irish': 'ga', 'italian': 'it', 'japanese': 'ja', 'javanese': 'jw', 
	'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 'kinyarwanda': 'rw', 'konkani': 'gom', 
	'korean': 'ko', 'krio': 'kri', 'kurdish (kurmanji)': 'ku', 'kurdish (sorani)': 'ckb', 
	'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 'lingala': 'ln', 
	'lithuanian': 'lt', 'luganda': 'lg', 'luxembourgish': 'lb', 'macedonian': 'mk', 
	'maithili': 'mai', 'malagasy': 'mg', 'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 
	'maori': 'mi', 'marathi': 'mr', 'meiteilon (manipuri)': 'mni-Mtei', 'mizo': 'lus', 
	'mongolian': 'mn', 'myanmar': 'my', 'nepali': 'ne', 'norwegian': 'no', 'odia (oriya)': 'or', 
	'oromo': 'om', 'pashto': 'ps', 'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 
	'punjabi': 'pa', 'quechua': 'qu', 'romanian': 'ro', 'russian': 'ru', 'samoan': 'sm', 
	'sanskrit': 'sa', 'scots gaelic': 'gd', 'sepedi': 'nso', 'serbian': 'sr', 'sesotho': 'st', 
	'shona': 'sn', 'sindhi': 'sd', 'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 
	'somali': 'so', 'spanish': 'es', 'sundanese': 'su', 'swahili': 'sw', 'swedish': 'sv', 
	'tajik': 'tg', 'tamil': 'ta', 'tatar': 'tt', 'telugu': 'te', 'thai': 'th', 'tigrinya': 'ti', 
	'tsonga': 'ts', 'turkish': 'tr', 'turkmen': 'tk', 'twi': 'ak', 'ukrainian': 'uk', 'urdu': 'ur', 
	'uyghur': 'ug', 'uzbek': 'uz', 'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 
	'yoruba': 'yo', 'zulu': 'zu'}
path = './tatoeba/'
http = 'https://downloads.tatoeba.org/exports/'

def test():
	print(gt().get_supported_languages(as_dict=True))

def maindatabase():
	con = sqlite3.connect("database.db")
	cur = con.cursor()
	return cur, con

def userdatabase(user):
	if (not os.path.exists('./user/')):
		os.mkdir('./user/')
	pon=sqlite3.connect(f"./user/{user}.db")
	return pon.cursor(), pon

def addlemma(words, lang, user):
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_known_lemma'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_known_lemma(lemma, count, date)")
	parsed =parser.parse(words, lang)
	lemmas = []
	for token in parsed:
		if (not token.lemma_ in lemmas):
			lemmas.append(token.lemma_)

	test = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	for lemma in test:
		if (lemma[0] in lemmas):
			lemmas.remove(lemma[0])

	pur.executemany(f"INSERT INTO {lang}_known_lemma VALUES (?, ?, ?)",[(lemma, 0, '1991-01-01') for lemma in lemmas])
	pon.commit()
	pon.close()

def updatelemma(lemma, lang, user):
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT count FROM {lang}_known_lemma WHERE lemma = ?",lemma).fetchone()
	pur.execute(f"UPDATE {lang}_known_lemma SET date = ?, count = ? WHERE lemma = ?",(datetime.date.today(), count[0]+1, lemma))
	pon.commit()
	pon.close()

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
		if (thing[0] in lemmas):
			pur.execute(f"DELETE FROM {lang}_known_lemma WHERE lemma = ?", thing)

	pon.commit()
	pon.close()

def getoldestlemma(lang, user, count):
	pur, pon = userdatabase(user)
	oldestlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma ORDER BY date LIMIT ?",(count,)).fetchall()
	pon.close()
	return oldestlemma

def getlemmainfo(word, lang, user):
	pur, pon = userdatabase(user)
	parsed = parser.parse(word, lang)
	info = pur.execute(f"SELECT lemma, count, date FROM {lang}_known_lemma WHERE lemma = ?",(parsed[0].lemma_,)).fetchone()
	pon.close()
	return info

def loadlang(lang):
	cur, con = maindatabase()
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
	con.commit()
	con.close()

def loadaux(aux):
	cur, con = maindatabase()
	filename =f"{aux}.tar.bz2"

	if (os.path.isfile(path + filename)):
		if (time.time()-os.path.getmtime(f"{path}{filename}")>604800):
			os.remove(path + filename)
			wget.download(f"{http}{filename}", path)
	else:
		wget.download(f"{http}{filename}", path)

	file = bz2.open(f"{path}{filename}", "r")

	cur.execute(f"DROP TABLE IF EXISTS {aux}")
	cur.execute(f"CREATE TABLE {aux}(id, data)")

	for line in file:
		try:
			line = str(line[:-1],'UTF-8').split("\t")[:2]
			cur.execute(f"INSERT INTO {aux} VALUES (?,?)",line)
		except:
			pass
	con.commit()
	con.close()
	return f'Finished rebuilding {aux}'

def processsentences(lang, user):#TODO refine grammar filter after grammar is refined
	cur, con = maindatabase()
	t = time.time()
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_available_sentences'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_available_sentences(id, count, date)")

	pur.execute(f"DROP TABLE IF EXISTS {lang}_close_lemma")
	pur.execute(f"CREATE TABLE {lang}_close_lemma(lemma, count)")

	knownlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	if (len(knownlemma)==0):
		return
	passgrammar = ['NUM', 'PUNCT', 'SYM', 'X']


	for row in cur.execute(f"SELECT id, text FROM {lang}").fetchall(): 
		parsed =parser.parse(row[1], lang)
		missing = []
		tokens = []

		for token in parsed:

			if (not(token.pos_ in passgrammar or (token.lemma_,) in knownlemma)):
				missing.append(token.lemma_)
			if (len(missing) == 2):
				break

		if (len(missing) == 0):
			if not row[0] in pur.execute(f"SELECT id FROM {lang}_available_sentences").fetchall():
				pur.execute(f"INSERT INTO {lang}_available_sentences VALUES (?, ?, ?)",(row[0], 0, '1991-01-01'))
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
	print("minutes to process ",(time.time()-t)/60)

def pickrandomsentence(lang, user):
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT COUNT(*) FROM {lang}_available_sentences").fetchone()[0]
	sentence = pur.execute(f"SELECT id FROM {lang}_available_sentences WHERE rowid = ?",(randrange(count),)).fetchone()[0]
	pon.close()
	return sentence

def picknextsentence(lang, user): 
	pur, pon = userdatabase(user)
	sentence =  pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchone()[0]
	pon.close()
	return sentence

def pickoldestlemmasentence(lang, user):
	pur, pon = userdatabase(user)
	old = getoldestlemma(lang, user, 1)
	bank = pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchall()
	for row in bank:
		text = cur.execute(f"SELECT text FROM {lang} WHERE id = ?", row).fetchone()
		parsed = parser.parse(text[0], lang)
		for token in parsed:
			if ((token.lemma_,) == old[0]):
				pon.close()
				return row[0]
	pon.close()

def gettext(num, lang):
	logger.warning('getting text')
	cur, con = maindatabase()
	text = cur.execute(f"SELECT text FROM {lang} WHERE id = ?", (num,)).fetchone()[0]
	con.close()
	return text

def marksentence(num, lang, user):
	cur, con = maindatabase()
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT count FROM '{lang}_available_sentences' WHERE id = ?",(num,)).fetchone()
	pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = ? WHERE id = ?",(datetime.date.today(), count[0] + 1, num))
	pon.commit()
	pon.close()
	con.close()

def getgoogle(num, targetlang, nativelang): 
	cur, con = maindatabase()
	info = cur.execute(f"SELECT text text FROM {targetlang} WHERE id = {num}").fetchone()
	con.close()
	return gt(source=gtd[targetlang], target=gtd[nativelang]).translate(info[0])

def gettranslations(num, lang):
	cur, con = maindatabase()
	translation = cur.execute(f"SELECT text FROM {lang} WHERE id IN (SELECT data FROM links WHERE id = '{num}')").fetchall()
	con.close()
	return translation

def getaudioids(num):
	cur, con = maindatabase()
	ids = cur.execute(f"SELECT data FROM sentences_with_audio WHERE id = '{num}'").fetchall()
	con.close()
	return ids

def getaudiofile(audioid):
	cur, con = maindatabase()
	if (not os.path.exists('./audio/')):
		os.mkdir('./audio/')
	num = cur.execute(f"SELECT id FROM sentences_with_audio WHERE data = ?", audioid).fetchone()[0]
	filename = './audio/' + num + '-' + audioid[0] + '.mp3'
	if (not os.path.isfile(filename)):
		wget.download(f"https://tatoeba.org/audio/download/{audioid[0]}", './audio/')
	con.close()
	return filename

def playaudio(filename): #TODO Currently direcly plays the audio but needs a sleep. 
	#Needs to be in a loop to remove sleep or move the playing of the file to html or javascript when thats setup
	p = vlc.MediaPlayer(filename)
	p.play()
	time.sleep(1)
	while (p.is_playing()):
		time.sleep(1)

def gettags(num):
	cur, con = maindatabase()
	tags = cur.execute(f"SELECT data FROM tags WHERE id = '{num}'").fetchall()
	con.close()
	return tags


if __name__ == '__main__' :
	nativelang = 'eng'
	targetlang = 'jpn'
	user = 'william'
	updatelemma("は", targetlang, user)
