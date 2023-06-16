from deep_translator import GoogleTranslator as gt
from random import randrange
from multiprocessing import Pool
import sqlite3, datetime, wget, os, bz2, time, logging, json, jaconv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gtd = {'cat': 'ca', 'cmn': 'zh-CN', #traditional chinese 'cmn': 'zh-TW', 
	'hrv': 'hr', 'dan': 'da', 'nld': 'nl', 'eng': 'en', 'fin': 'fi', 'fra': 'fr',
	'deu': 'de', 'ell': 'el', 'ita': 'it', 'jpn': 'ja', 'kor': 'ko',
	'lit': 'lt', 'mkd': 'mk', 'nob': 'no', 'pol': 'pl', 'por': 'pt', 
	'ron': 'ro', 'rus': 'ru', 'spa': 'es', 'swe': 'sv', 'ukr': 'uk'}

def addlemmagrammar(words, lang, user):
	pur, pon = userdatabase(user)
	cur, con = langdatabase(lang)

	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_known_lemma'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_known_lemma(lemma, count, date)")
	parsed =parser.parse(words, lang)
	grammar = {'tag':{}, 'POS':{}, 'ent_type':{}}
	lemmas = []
	for token in parsed:
		lemma = token.lemma_.lower().strip()
		if (not lemma in lemmas):
			lemmas.append(lemma)

		tokendict = token.morph.to_dict()
		for morph in tokendict:
			if (morph != 'Reading'):
				if (not morph in grammar):
					grammar[morph] = {}
				if (not tokendict[morph] in grammar[morph]):
					grammar[morph][tokendict[morph]] = {'unknown': 0, 'known': 1, 'focus': 0}
		if (not token.tag_ in grammar['tag']):
			grammar['tag'][token.tag_] = {'unknown': 0, 'known': 1, 'focus': 0}
		if (not token.pos_ in grammar['POS']):
			grammar['POS'][token.pos_] = {'unknown': 0, 'known': 1, 'focus': 0}
		if (not token.ent_type_ in grammar['ent_type'] and not token.ent_type_ == ''):
			grammar['ent_type'][token.ent_type_] = {'unknown': 0, 'known': 1, 'focus': 0}

	test = pur.execute(f"SELECT lemma FROM {lang}_known_lemma").fetchall()
	for lemma in test:
		if (lemma[0] in lemmas):
			lemmas.remove(lemma[0])

	pur.executemany(f"INSERT INTO {lang}_known_lemma VALUES (?, ?, ?)",[(lemma, 0, '1991-01-01') for lemma in lemmas])
	logger.info(f"New lemma inserted into {user}'s database:{lemmas}")
	pon.commit()
	pon.close()
	con.close()
	return lemmas, grammar

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
	blob = json.loads(cur.execute(f"SELECT id, json FROM {lang}_db WHERE id = {str(num)}").fetchone()['json'])
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

def processsubs(targetlang, nativelangs): 
	t = time.time()
	cur, con = langdatabase(targetlang)
	subs = ['lemma','tag','ent_type', 'POS']
	things = {}
	for sub in subs:
		cur.execute(f"DROP TABLE IF EXISTS {targetlang}_{sub}")
		cur.execute(f"CREATE TABLE {targetlang}_{sub}({sub}, count, translation)")
		things[sub]={}
	#i = 0 
	for row in cur.execute(f"SELECT id, json FROM {targetlang}_db").fetchall():
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

def processmorph(targetlang, nativelangs): 
	t = time.time()
	cur, con = langdatabase(targetlang)
	grammar = {}
	for row in cur.execute(f"SELECT id, json FROM {targetlang}_db").fetchall():
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

def processsentences(lang, user): 
	t = time.time()
	cur, con = langdatabase(lang)
	pur, pon = userdatabase(user)

	#pur.execute(f"DROP TABLE IF EXISTS {lang}_available_sentences") #only 
	if (pur.execute(f"SELECT name FROM sqlite_master WHERE name = '{lang}_available_sentences'").fetchone() is None):
		pur.execute(f"CREATE TABLE {lang}_available_sentences(id, count, date, active, audio, focus, lemma)")

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
	for row in cur.execute(f"SELECT id, json, audio, available FROM {lang}_db").fetchall(): 
		if (row['available'] == '0'):
			if (row['id'] in already):
				pur.execute(f"UPDATE {lang}_available_sentences SET active = ? WHERE id = ?",(0, row['id']))
			break

		pt = time.time()
		parsed = json.loads(row['json'])
		parsertime = parsertime + time.time() - pt
		missinglemma = []
		missinggrammar = []
		lemma =[]
		focus = []
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
					elif (grammar[thing][token['morph'][thing]]['focus'] and not f"{thing} {token['morph'][thing]}" in focus):
						focus.append(token['morph'][thing])
				elif (grammar[thing][token[thing]]['unknown']):
					unknown = True
					break
				elif (not grammar[thing][token[thing]]['known'] and not f"{thing} {token[thing]}" in missinggrammar):
						missinggrammar.append(f"{thing} {token[thing]}")
				elif (grammar[thing][token[thing]]['focus'] and not f"{thing} {token[thing]}" in missinggrammar):
					focus.append(token[thing])

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

			lemma.append(token['lemma'])


		lenlemma =len(missinglemma)
		lengrammar = len(missinggrammar)
		if (lenlemma + lengrammar == 0):
			if (not row['id'] in already):
				pur.execute(f"INSERT INTO {lang}_available_sentences VALUES (?, ?, ?, ?, ?, ?, ?)",(row['id'], 0, '1991-01-01', 1, row['audio'], json.dumps(focus), json.dumps(lemma)))
				logger.info(f"Sentence {row['id']} added to available sentences in {lang} for {user}")
			else:
				pur.execute(f"UPDATE {lang}_available_sentences SET active = ?, audio = ?, focus = ?, lemma = ? WHERE id = ?",(1, row['audio'], json.dumps(focus), json.dumps(lemma), row['id']))
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

def pullgrammartrans(lang):
	cur, con = langdatabase(lang)	
	grammar = {}
	subs = ['tag', 'ent_type', 'POS']
	for row in cur.execute(f"SELECT morph FROM {lang}_morphs").fetchall():
		subs.append(sqlsafe(row['morph']))

	for sub in subs:
		grammar[sub] = {}
		for each in cur.execute(f"SELECT {sub}, count, translation FROM {lang}_{sub}").fetchall():
			grammar[sub][each[sub]] = {'count':each['count'], 'translation': json.loads(each['translation'])}


	con.commit()
	con.close()
	return grammar

def pushusergrammar(lang, user, grammar):
	pur, pon = userdatabase(user)

	for sub in grammar:
		for thing in grammar[sub]:
			for known in grammar[sub][thing]:
				pur.execute(f"UPDATE {lang}_{sub} SET {known}=? WHERE {sub} = ?",(grammar[sub][thing][known], thing))

	pon.commit()
	pon.close()

def additionalinfo(lang, sentence): 
	info = None
	if (lang == 'jpn'):
		tokens = json.loads(sentence['json'])
		reading = ""
		for token in tokens:
			if ('Reading' in token['morph'] and token['text'] != '？'):
				reading += '  ' + token['morph']['Reading']
			if token['text'] == '？':
				reading += '?'
		info = jaconv.kata2hira(reading)
	return info

def picksentence(lang, user, way = 'random'): #TODO Needs to be improved auto check old lemma and focus grammar also SRS with alreaady seen
	pur, pon = userdatabase(user)
	if way == 'random':
		count = pur.execute(f"SELECT COUNT(*) FROM {lang}_available_sentences").fetchone()[0]
		number =randrange(1,count)
		sentence = pur.execute(f"SELECT id FROM {lang}_available_sentences WHERE rowid = ?",(number,)).fetchone()['id']
	elif way == 'oldlemma':
		old = getoldestlemma(lang, user, 1)
		bank = pur.execute(f"SELECT id, lemma FROM {lang}_available_sentences ORDER BY count").fetchall()
		for row in bank:
			if (old[0] in json.loads(row['lemma'])):
				sentence =  row['id']
				break
	if (not sentence):
		sentence =  pur.execute(f"SELECT id FROM {lang}_available_sentences ORDER BY count").fetchone()['id']
	pon.close()
	logger.info(f'{way} {sentence} picked for {user}')
	cur, con = langdatabase(lang)	
	sentence = cur.execute(f"SELECT id, text, json, audio, trans, tags, control FROM {lang}_db WHERE id = ?", (sentence,)).fetchone()
	con.close()
	return sentence

def marksentence(num, lang, user):
	pur, pon = userdatabase(user)
	count = pur.execute(f"SELECT count FROM '{lang}_available_sentences' WHERE id = {str(num)}").fetchone()
	date = str(datetime.date.today())
	pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = {count['count'] + 1} WHERE id = {num}",(date,))
	#pur.execute(f"UPDATE {lang}_available_sentences SET date = ?, count = ? WHERE id = ?",(datetime.date.today(), count['count']+1, num))
	pon.commit()
	pon.close()
	logger.info(f'Marking sentence, {num} as read by {user}')

def getgoogle(text, targetlang, nativelang): 
	translation = gt(source=gtd[targetlang], target=gtd[nativelang]).translate(text)
	logger.info(f'Returning google translation for sentence, {text} in {nativelang}')
	return translation

def gettrans(num):
	lur, lon = langdatabase('all_lang')
	ids = lur.execute(f"SELECT data FROM links WHERE id = '{num}'").fetchall()
	ids = [i['data'] for i in ids]
	lon.close()
	return ids

def getlations(ids, lang):
	cur, con = langdatabase(lang)
	if ids == []:
		translations = None
	else:
		translations =[]
		for senid in ids:
			temp = cur.execute(f"SELECT text FROM {lang}_db WHERE id = ? ",(senid,)).fetchone()
			if temp != None:
				translations.append(temp['text'])
	con.close()
	logger.info(f'Returning database translations for sentence {num} in {lang}')
	return translations

def getaudiofiles(num):
	lur, lon = langdatabase('all_lang')
	ids = lur.execute(f"SELECT id, data FROM sentences_with_audio WHERE id = '{num}'").fetchall()
	files = []
	for audioid in ids:
		filename = audioid['id'] + '-' + audioid['data'] + '.mp3'
		filepath = './JTRL/static/audio/' + filename
		files.append(filename)
		if (not os.path.isfile(filepath)):
			wget.download(f"https://tatoeba.org/audio/download/{audioid['data']}", './JTRL/static/audio/')
			logger.info(f'Audio file for {audioid} Downloaded')
		else:
			logger.info(f'Audio file for {filename} already downloaded')
	lon.close()
	return files



if __name__ == '__main__' :
	#Testing stuff
	#nativelang = 'eng'
	nativelangs = {'eng':True, 'spa':True, 'deu':False}
	targetlang = 'deu'
	targetlangs = ['jpn', 'spa', 'deu']
	user = 2
	print("\n\n")
	logger.info(f'database.py run as main')
	test1 = ["私は眠らなければなりません。", "きみにちょっとしたものをもってきたよ。", "何かしてみましょう。", "何してるの？", "今日は６月１８日で、ムーリエルの誕生日です！"]
	test2 = "犬"
	#for lang in targetlangs:
	#	createlangdb(targetlang)
	resetdb('audio', targetlangs)
		#processsubs(lang, nativelangs)
		#processmorph(lang, nativelangs)

	with Pool(3) as p:
		for column in ['json', 'audio', 'trans']:
			info = [(column, targetlang) for targetlang in targetlangs]
			p.starmap(filldb, info) 