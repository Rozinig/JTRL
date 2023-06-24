
from random import randrange
from multiprocessing import Pool
import sqlite3, datetime, wget, os, bz2, time, logging, json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gtd = 0

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



if __name__ == '__main__' :
	nativelangs = {'eng':True, 'spa':True, 'deu':False}
	targetlang = 'deu'
	targetlangs = ['jpn', 'spa', 'deu']
	user = 2
	print("\n\n")
	logger.info(f'database.py run as main')
	test1 = ["私は眠らなければなりません。", "きみにちょっとしたものをもってきたよ。", "何かしてみましょう。", "何してるの？", "今日は６月１８日で、ムーリエルの誕生日です！"]
	test2 = "犬"