from deep_translator import GoogleTranslator as gt
from random import randrange
#import vlc
import sqlite3, datetime, wget, os, bz2, time, logging, json, jaconv
	
path = './tatoeba/'
http = 'https://downloads.tatoeba.org/exports/'
dirs = ['./lang/', './user/', './tatoeba/', './static/', './JTRL/static/audio/', './logs/']
for pathway in dirs:
	if (not os.path.exists(pathway)):
		os.mkdir(pathway)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if __name__ == '__main__':
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	fh = logging.FileHandler('./logs/database.log')
	fh.setLevel(logging.DEBUG)
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	import parser
else:
	from . import parser

gtd = {'cat': 'ca', 'cmn': 'zh-CN', #traditional chinese 'cmn': 'zh-TW', 
	'hrv': 'hr', 'dan': 'da', 'nld': 'nl', 'eng': 'en', 'fin': 'fi', 'fra': 'fr',
	'deu': 'de', 'ell': 'el', 'ita': 'it', 'jpn': 'ja', 'kor': 'ko',
	'lit': 'lt', 'mkd': 'mk', 'nob': 'no', 'pol': 'pl', 'por': 'pt', 
	'ron': 'ro', 'rus': 'ru', 'spa': 'es', 'swe': 'sv', 'ukr': 'uk'}


parser = parser.parser(fast=True)

def test():
	i=0
	while (i<=100):
		printProgressBar (i, 100, prefix = 'How far', suffix = 'Complete', decimals = 1, length = 100, fill = '█', printEnd = "\r")
		time.sleep(1)
		i+=1
	#print(gt().get_supported_languages(as_dict=True))

def database(): 
	don = sqlite3.connect("database.db")
	don.row_factory = sqlite3.Row
	dur = lon.cursor()
	logger.info('Connected to main Database.')
	return dur, don

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def langdatabase(lang): 
	con = sqlite3.connect(f"./lang/{lang}.db")
	con.row_factory = sqlite3.Row
	cur = con.cursor()
	logger.info(f'Connected to {lang} Database.')
	return cur, con

def userdatabase(user): 
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
		lemma = token.lemma_.lower().strip()
		if (not lemma in lemmas):
			lemmas.append(lemma)

	test = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	for lemma in test:
		if (lemma[0] in lemmas):
			lemmas.remove(lemma[0])

	pur.executemany(f"INSERT INTO {lang}_known_lemma VALUES (?, ?, ?)",[(lemma, 0, '1991-01-01') for lemma in lemmas])
	logger.info(f"New lemma inserted into {user}'s database:{lemmas}")
	pon.commit()
	pon.close()
	return lemmas

def updatelemma(lemma, lang, user): 
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT count FROM {lang}_known_lemma WHERE lemma = '{lemma}'").fetchone()
	if count != None:
		pur.execute(f"UPDATE {lang}_known_lemma SET date = ?, count = ? WHERE lemma = ?",(datetime.date.today(), count['count']+1, lemma))
		logger.info(f'Lemma, {lemma}, updated for {user}')
	else:
		logger.info(f"Lemma, {lemma}, was not in {user}'s database")
	pon.commit()
	pon.close()

def updatesentencelemma(num, lang, user):
	cur, con = langdatabase(lang)
	blob = json.loads(cur.execute(f"SELECT id, json FROM {lang}_json WHERE id = {str(num)}").fetchone()['json'])
	con.close()
	for each in blob:
		updatelemma(each["lemma"], lang, user)

def removelemma(words, lang, user):
	pur, pon = userdatabase(user)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_known_lemma'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_known_lemma(lemma, count, date)")
	parsed =parser.parse(words, lang)
	lemmas = []
	for token in parsed:
		lemma = token.lemma_.lower().strip()
		if (not lemma in lemmas):
			lemmas.append(lemma)

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
	lemma = parsed[0].lemma_.lower().strip()
	info = pur.execute(f"SELECT lemma, count, date FROM {lang}_known_lemma WHERE lemma = ?",(lemma,)).fetchone()
	pon.close()
	logger.info(f"{info} found for {user}'s word: {word}")
	return info

def getalllemmainfo(lang,user):
	pur, pon = userdatabase(user)
	info = pur.execute(f"SELECT lemma, count, date FROM {lang}_known_lemma ").fetchall()
	pon.close()
	logger.info(f"Retrieved all known lemma for {user}")
	return info

def loadlang(lang):
	cur, con = langdatabase(lang)
	filename =f"{lang}_sentences.tsv.bz2"


	if (os.path.isfile('./tatoeba/' + filename)):
		if (time.time()-os.path.getmtime(f"./tatoeba/{filename}")>604800):
			os.remove('./tatoeba/' + filename)
			wget.download(f"{http}per_language/{lang}/{filename}", './tatoeba/')
	else:
		wget.download(f"{http}per_language/{lang}/{filename}", './tatoeba/')

	file = bz2.open(f"./tatoeba/{filename}", "r")

	cur.execute(f"DROP TABLE IF EXISTS {lang}")
	cur.execute(f"CREATE TABLE {lang}('id' INTEGER PRIMARY KEY, text) WITHOUT ROWID")

	for line in file:
		line = str(line[:-1],'UTF-8').split("\t")
		line = [line[0], line[2]]
		cur.execute(f"INSERT INTO {lang} VALUES (?,?)",line)
	logger.info(f"{lang} database for language, {lang} has been updated")
	con.commit()
	con.close()

def loadaux(aux):
	lur, lon = langdatabase('all_lang')
	filename =f"{aux}.tar.bz2"

	if (os.path.isfile('./tatoeba/' + filename)):
		if (time.time()-os.path.getmtime(f"./tatoeba/{filename}")>604800):
			os.remove('./tatoeba/' + filename)
			wget.download(f"{http}{filename}", './tatoeba/')
	else:
		wget.download(f"{http}{filename}", './tatoeba/')

	file = bz2.open(f"./tatoeba/{filename}", "r")

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

def processlangjson(lang):
	t = time.time()
	cur, con = langdatabase(lang)
	cur.execute(f"DROP TABLE IF EXISTS {lang}_json")
	cur.execute(f"CREATE TABLE {lang}_json(id, json)")
	i = 0
	for row in cur.execute(f"SELECT id, text FROM {lang}").fetchall(): 
		i += 1
		if (i%1000 == 0):
			print(f"{i} sentences completed for {lang}")
		parsed =parser.parse(row['text'], lang)
		tokens =[]
		for token in parsed:
			bit = {'text':token.text, 'lemma':token.lemma_.lower().strip(), 'POS':token.pos_, 'ent_type':token.ent_type_, 'tag':token.tag_, 'morph':token.morph.to_dict()}
			tokens.append(bit)
		cur.execute(f"INSERT INTO {lang}_json VALUES (?,?)",(row['id'], json.dumps(tokens, ensure_ascii=False).encode('utf8')))
	con.commit()
	con.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed sentences to json in {lang}")
	logger.info(f"{lang} processed to SQL with Json lemma and Grammar")

def processsubsjson(targetlang, nativelangs): 
	t = time.time()
	cur, con = langdatabase(targetlang)
	subs = ['lemma','tag','ent_type', 'POS']
	things = {}
	for sub in subs:
		cur.execute(f"DROP TABLE IF EXISTS {targetlang}_{sub}")
		cur.execute(f"CREATE TABLE {targetlang}_{sub}({sub}, count, translation)")
		things[sub]={}
	#i = 0 
	for row in cur.execute(f"SELECT id, json FROM {targetlang}_json").fetchall():
		#i += 1
		#if (i%100 == 0):
		#	print(i, (time.time()-t)/60)
		for info in json.loads(row['json']):
			for sub in subs:
				if (info[sub] in things[sub]):
					things[sub][info[sub]] += 1
				else:
					things[sub][info[sub]] = 1
	for sub in subs:
		for key in things[sub]:
			trans = {}
			if (sub != 'lemma'):
				for lang in nativelangs:
					if not nativelangs[lang] or lang == targetlang:
						continue
					trans[lang] = gt(source=gtd[targetlang], target=gtd[lang]).translate(key)
			cur.execute(f"INSERT INTO {targetlang}_{sub} VALUES (?,?,?)",(key, things[sub][key], json.dumps(trans)))
	con.commit()
	con.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed json to {subs} in {targetlang}")

def processmorphjson(targetlang, nativelangs): 
	t = time.time()
	cur, con = langdatabase(targetlang)
	grammar = {}
	for row in cur.execute(f"SELECT id, json FROM {targetlang}_json").fetchall():
		for info in json.loads(row['json']):
			for morph in info['morph']:
				if morph == "Reading":
					continue
				if not morph in grammar:
					grammar[morph]= {}
				if info['morph'][morph] in grammar[morph]:
					grammar[morph][info['morph'][morph]] += 1
				else:
					grammar[morph][info['morph'][morph]] = 1

	cur.execute(f"DROP TABLE IF EXISTS {targetlang}_morphs")
	cur.execute(f"CREATE TABLE {targetlang}_morphs(morph, translation)")
	for morph in grammar:
		trans = {}
		for lang in nativelangs:
			if not nativelangs[lang] or lang == targetlang:
				continue
			trans[lang] = gt(source=gtd[targetlang], target=gtd[lang]).translate(morph)
		cur.execute(f"INSERT INTO {targetlang}_morphs VALUES (?,?)",(morph, json.dumps(trans)))

		cur.execute(f"DROP TABLE IF EXISTS {targetlang}_{sqlsafe(morph)}")
		cur.execute(f"CREATE TABLE {targetlang}_{sqlsafe(morph)}('{sqlsafe(morph)}', count, translation)") # , explain
		for thing in grammar[morph]:
			trans = {}
			for lang in nativelangs:
				if not nativelangs[lang] or lang == targetlang:
					continue
				try:
					trans[lang] = gt(source=gtd[targetlang], target=gtd[lang]).translate(thing)
				except:
					logger.info(f"[{thing}] didn't translate from {targetlang} to {lang}.")
					trans[lang] = thing
			cur.execute(f"INSERT INTO {targetlang}_{sqlsafe(morph)} VALUES (?,?,?)",(thing, grammar[morph][thing], json.dumps(trans))) #, parser.explain(thing)

	con.commit()
	con.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to process json to grammar in {targetlang}")

def processsentencesjson(lang, user): #check for forgein words
	t = time.time()
	cur, con = langdatabase(lang)
	pur, pon = userdatabase(user)

	#pur.execute(f"DROP TABLE IF EXISTS {lang}_available_sentences") #only 
	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_available_sentences'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_available_sentences(id, count, date, active)")

	pur.execute(f"DROP TABLE IF EXISTS {lang}_close_lemma")
	pur.execute(f"CREATE TABLE {lang}_close_lemma(lemma, count)")

	pur.execute(f"DROP TABLE IF EXISTS {lang}_close_grammar")
	pur.execute(f"CREATE TABLE {lang}_close_grammar(grammar, count)")

	knownlemma = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	if (len(knownlemma)==0):
		return

	grammar = pullusergrammar(lang, user)
	parsertime = 0
	
	already =pur.execute(f"SELECT id FROM {lang}_available_sentences").fetchall()
	already = [i['id'] for i in already]
	knownlemma = [lemma['lemma']for lemma in knownlemma]
	for row in cur.execute(f"SELECT id, json FROM {lang}_json").fetchall(): 
		pt = time.time()
		parsed = json.loads(row['json'])
		parsertime = parsertime + time.time() - pt
		missinglemma = []
		missinggrammar = []
		for token in parsed:
			unknown = False
			for thing in grammar:
				#check unknowns and knowns
				#print(thing)
				if (not thing in ['tag', 'ent_type', 'POS']):
					#print ('run\n', thing, '\n', grammar[thing], '\n', token['morph'][thing], '\n\n')
					if (not thing in token['morph']):
						pass
					elif (grammar[thing][token['morph'][thing]]['unknown']):
						unknown = True
						break
					elif (not grammar[thing][token['morph'][thing]]['known'] and not f"{thing} {token['morph'][thing]}" in missinggrammar):
						missinggrammar.append(f"{thing} {token['morph'][thing]}")
				elif (grammar[thing][token[thing]]['unknown']):
					unknown = True
					break
				elif (not grammar[thing][token[thing]]['known'] and not f"{thing} {token[thing]}" in missinggrammar):
						missinggrammar.append(f"{thing} {token[thing]}")
				#if (len(missinggrammar) > 1): #compare processing speed with and without
				#	break
			if (unknown):
				continue

			if (len(missinggrammar) > 1):
				break

			if (not(token['lemma'] in knownlemma)):
				missinglemma.append(token['lemma'])

			if (len(missinglemma) + len(missinggrammar) > 1):
				break

		lenlemma =len(missinglemma)
		lengrammar = len(missinggrammar)
		if (lenlemma + lengrammar == 0):
			if (not row['id'] in already):
				pur.execute(f"INSERT INTO {lang}_available_sentences VALUES (?, ?, ?, ?)",(row['id'], 0, '1991-01-01', 1))
				logger.info(f"Sentence {row['id']} added to available sentences in {lang} for {user}")
			else:
				pur.execute(f"UPDATE {lang}_available_sentences SET active = ? WHERE id = ?",(1, row['id']))
				logger.info(f"Sentence {row['id']} already in available sentences in {lang} for {user}")
		elif (row['id'] in already):

			pur.execute(f"UPDATE {lang}_available_sentences SET active = ? WHERE id = ?",(0, row['id']))

			if (lenlemma == 1 and lengrammar == 0):
				count = pur.execute(f"SELECT count FROM '{lang}_close_lemma' WHERE lemma = ?",(missinglemma[0],)).fetchone()
				if count:
					pur.execute(f"UPDATE {lang}_close_lemma SET count = ? WHERE lemma = ?",(count['count'] + 1, missinglemma[0]))
				else:
					pur.execute(f"INSERT INTO {lang}_close_lemma VALUES (?,?)",(missinglemma[0], 1))
			elif (lengrammar == 1 and lenlemma == 0):
				count = pur.execute(f"SELECT count FROM '{lang}_close_grammar' WHERE grammar = ?",(missinggrammar[0],)).fetchone()
				if count:
					pur.execute(f"UPDATE {lang}_close_grammar SET count = ? WHERE grammar = ?",(count['count'] + 1, missinggrammar[0]))
				else:
					pur.execute(f"INSERT INTO {lang}_close_grammar VALUES (?,?)",(missinggrammar[0], 1))
	con.commit()
	con.close()
	pon.commit()
	pon.close()
	totaltime = (time.time()-t)/60
	logger.info(f"Took {totaltime} mintues to proceed sentences from json in {lang} for {user}")
	parsertime = parsertime/60
	logger.info(f'Language json retrival took {parsertime} mintues')

def createusergrammar(lang, user):
	cur, con = langdatabase(lang)
	pur, pon = userdatabase(user)

	pur.execute(f"DROP TABLE IF EXISTS {lang}_morphs")
	pur.execute(f"CREATE TABLE {lang}_morphs(morph)")

	for row in cur.execute(f"SELECT morph FROM {lang}_morphs").fetchall():
		pur.execute(f"INSERT INTO {lang}_morphs VALUES (?)",(row['morph'],))
		pur.execute(f"DROP TABLE IF EXISTS {lang}_{sqlsafe(row['morph'])}")
		pur.execute(f"CREATE TABLE {lang}_{sqlsafe(row['morph'])}('{sqlsafe(row['morph'])}', unknown, known, focus)")
		for thing in cur.execute(f"SELECT {sqlsafe(row['morph'])} FROM {lang}_{sqlsafe(row['morph'])}").fetchall():
			pur.execute(f"INSERT INTO {lang}_{sqlsafe(row['morph'])} VALUES (?,?,?,?)",(thing[sqlsafe(row['morph'])], False, False, False))

	for sub in ['tag', 'ent_type', 'POS']:
		pur.execute(f"DROP TABLE IF EXISTS {lang}_{sub}")
		pur.execute(f"CREATE TABLE {lang}_{sub}({sub}, unknown, known, focus)")
		for row in cur.execute(f"SELECT {sub} FROM {lang}_{sub}").fetchall():
			if (sub == 'POS' and (row[sub] == 'X' or row[sub] == 'SYM' or row[sub] == 'PUNCT')):
				pur.execute(f"INSERT INTO {lang}_{sub} VALUES (?,?,?,?)",(row[sub], True, False, False))
			else:
				pur.execute(f"INSERT INTO {lang}_{sub} VALUES (?,?,?,?)",(row[sub], False, False, False))

	logger.info(f"Created {lang} gammar for {user}")
	con.close()
	pon.commit()
	pon.close()

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

def pushusergrammar(lang, user, grammar):
	pur, pon = userdatabase(user)

	for sub in grammar:
		for thing in grammar[sub]:
			for known in grammar[sub][thing]:
				pur.execute(f"UPDATE {lang}_{sub} SET {known}=? WHERE {sub} = ?",(grammar[sub][thing][known], thing))

	pon.commit()
	pon.close()

def pullusergram(lang, user):
	#Wrapper to allow grammar to be refined for Spacy's grammar to Language learner grammar needs be the opposite of pushusergram
	grammar = pullusergrammar(lang, user)
	print(grammar['ent_type'].pop('', None))
	return grammar

def pushusergram(lang, user, grammar):
	#Wrapper to allow grammar to be refined for Spacy's grammar to Language learner grammar needs be the opposite of pullusergram
	grammar['ent_type'][''] = {'unknown': 0, 'known': 1, 'focus': 0}
	return pushusergrammar(lang, user, grammar)

def additionalinfo(lang, num):
	cur, con = langdatabase(lang)	
	if (lang == 'jpn'):
		print(num)
		info = cur.execute(f"SELECT id, json FROM {lang}_json WHERE id = {num}").fetchone()
		print(info)
		tokens = json.loads(info['json'])
		reading = ""
		for token in tokens:
			if ('Reading' in token['morph'] and token['text'] != '？'):
				reading += '  ' + token['morph']['Reading']
			if token['text'] == '？':
				reading += '?'
		return jaconv.kata2hira(reading)
	con.close()
	return None

def touchlangdb(lang, db):
	cur, con = langdatabase(lang)	
	touch = cur.execute(f"SELECT name FROM sqlite_master WHERE name = '{db}'").fetchone()
	con.close()
	if (touch is None):
		return False
	return True

def touchuserdb(lang, user, db):
	pur, pon = userdatabase(user)
	touch = pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{db}'").fetchone()
	if (touch is None):
		pon.close()
		return False
	count = pur.execute(f"SELECT COUNT(*) FROM {db}").fetchone()[0]
	pon.close()
	if (count == 0):
		return False
	return True

def pickrandomsentence(lang, user):
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT COUNT(*) FROM {lang}_available_sentences").fetchone()[0]
	number =randrange(count)
	print(number)
	sentence = pur.execute(f"SELECT id FROM {lang}_available_sentences WHERE rowid = ?",(number,)).fetchone()['id']
	pon.close()
	logger.info(f'Random sentence {sentence} picked for {user}')
	return sentence

def picknextsentence(lang, user): 
	pur, pon = userdatabase(user)
	sentence =  pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchone()['id']
	pon.close()
	logger.info(f'The next sentence, {sentence} picked for {user}')
	return sentence

def pickoldestlemmasentence(lang, user): 
	pur, pon = userdatabase(user)
	old = getoldestlemma(lang, user, 1)
	bank = pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchall()
	for row in bank:
		text = cur.execute(f"SELECT text FROM {lang} WHERE id = ?", row).fetchone()
		parsed = parser.parse(text['text'], lang)
		for token in parsed:
			if ((token.lemma_.lower().strip(),) == old[0]):
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
	count = pur.execute(f"SELECT count FROM '{lang}_available_sentences' WHERE id = {str(num)}").fetchone()
	date = str(datetime.date.today())
	pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = {count['count'] + 1} WHERE id = {num}",(date,))
	#pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = ? WHERE id = ?",(datetime.date.today(), count['count']+1, num))
	pon.commit()
	pon.close()
	logger.info(f'Marking sentence, {num} as read by {user}')

def getgoogle(num, targetlang, nativelang): 
	cur, con = langdatabase(targetlang)
	info = cur.execute(f"SELECT text FROM {targetlang} WHERE id = {num}").fetchone()
	con.close()
	#print(nativelang)
	translation = gt(source=gtd[targetlang], target=gtd[nativelang]).translate(info['text'])
	logger.info(f'Returning google translation for sentence, {num} in {nativelang}')
	return translation

def gettranslations(num, lang): 
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
	num = lur.execute(f"SELECT id FROM sentences_with_audio WHERE data = ?", audioid).fetchone()['id']
	filename = num + '-' + audioid[0] + '.mp3'
	filepath = './JTRL/static/audio/' + filename
	if (not os.path.isfile(filepath)):
		wget.download(f"https://tatoeba.org/audio/download/{audioid[0]}", './JTRL/static/audio/')
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

def sqlsafe(morph):
	morph1 = morph.split(']')
	morph2 = morph1[0].split('[')
	morph = "_".join(morph2)
	return morph



if __name__ == '__main__' :
	#Testing stuff
	#nativelang = 'eng'
	nativelangs = {'eng':True, 'spa':True, 'deu':False}
	targetlang = 'jpn'
	targetlangs = ['jpn', 'spa', 'deu']
	user = 2
	print("\n\n")
	logger.info(f'database.py run as main')
	test1 = ["私は眠らなければなりません。", "きみにちょっとしたものをもってきたよ。", "何かしてみましょう。", "何してるの？", "今日は６月１８日で、ムーリエルの誕生日です！"]
	test2 = "犬"
	#for targetlang in targetlangs:
		#print(parser.sources(targetlang))
	#	processmorphjson(targetlang, nativelangs)
	#	processsubsjson(targetlang, nativelangs)
	#createusergrammar('jpn', user)
	#x = pullusergrammar('jpn', user)
	#print(x['Polarity']['Neg']['known'])
	#x['Polarity']['Neg']['known'] = True
	#pushusergrammar('jpn', user, x)
	#print(pullusergrammar('jpn', user)['Polarity']['Neg']['known'])
	#test()
	#for words in test1:
	#	addlemma(words, targetlang, user)
	#processsentencesjson(targetlang, user)
	#updatesentencelemma(1297, targetlang, user)
	#test()
	#processlangjson(targetlang)
	#processsentencesjson(targetlang, user)
	#processsentencesraw(targetlang, user)
	#updatelemma("は", targetlang, user)
	#print(getalllemmainfo(targetlang, user)[0]['lemma'])
	#print("Japanse Json? ", touchjson(targetlang))
	#print("English Json? ", touchjson(nativelang))