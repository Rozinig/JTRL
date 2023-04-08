from flask import Flask
from markupsafe import escape
from database import *
import time

app = Flask(__name__)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

fh = logging.FileHandler('main.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = app.logger
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)

databaselogger = logging.getLogger('database')
databaselogger.addHandler(ch)
databaselogger.addHandler(fh)



nativelang = 'eng'
targetlang = 'jpn'
user = 'william'

header = '<meta name="viewport" content="width=device-width, initial-scale=1.0"><style>p {  width: 300px; word-wrap: break-word;    font-size: 20px;} button {font-size:20px;} </style>'


if (0):
	print('rebuilding database')
	t = time.time()
	loadlang(targetlang)
	loadlang(nativelang)
	print(time.time()-t)



'''tes = ["私は眠らなければなりません。", "きみにちょっとしたものをもってきたよ。", "何かしてみましょう。", "何してるの？", "今日は６月１８日で、ムーリエルの誕生日です！"]
for test in tes: 
	database.addlemma(test, targetlang, user)
database.updatelemma("は", targetlang, user)
database.removelemma("は", targetlang, user)

print(database.getgoogle(1297, targetlang, nativelang))
x = database.getaudioids(4704)
print(database.gettags(4704))
print(database.gettranslations(1297, nativelang))
print(database.gettranslations(4703, nativelang))
database.processsentences(targetlang, user)
print(database.picknextsentence(targetlang, user))
print(database.marksentence(num, targetlang, user))
print(database.getoldestlemma(targetlang, user, 10))
print(database.getlemmainfo("は", targetlang, user))
print(database.pickrandomsentence(targetlang, user))
print(database.pickoldestlemmasentence(targetlang, user))
print(database.gettext(4704, targetlang))
y = database.getaudiofile(x[0])
database.playaudio(y)
test = dictionary.define()
for things in test:
	print(things)'''


    
@app.route("/")
def home():
	updatelemma("は", targetlang, user)
	x = picknextsentence(targetlang,user)
	y = gettext(x, targetlang)
	logger.warning('home')
	return header + f'<p>test {x}, {y}</p>'

@app.route("/<lang>")
def lang(lang):
	lang=escape(lang)
	return header + f'<p>{lang}test</p>'

@app.route("/rebuild/<lang>")
def rebuildlang(lang):
	lang=escape(lang)
	return header + f'<p>rebuild {lang}</p>'

@app.route("/rebuild/base")
def rebuildbase():
	#x = loadaux('sentences_with_audio') #not limited to creative commons
	#y = loadaux('tags')
	#z = loadaux('links')
	return header + f'<p>test</p>'

@app.route("/rebuild")
def rebuild():
	return header + '<p>Do you want to rebuild stuff?</p>'

#initialize
	#if all sentences db doesn't exist do that
	#option to add known words
	#show known grammar optionshttps://tatoeba.org/audio/download/1682
	#update avaible sentence db
	#option to practice
	#show one missing lemmas

#build all sentences db based on target and source language
	#save possible grammar to list


#take known lemmas and cross reference with all sentence db
	#produce list of one missing sentences



