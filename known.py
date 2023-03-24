import ja_parser
import sqlite3
import datetime

con = sqlite3.connect("database.db")
cur = con.cursor()
if (cur.execute("SELECT name FROM sqlite_master WHERE name = 'known'").fetchone() is None):
	cur.execute("CREATE TABLE known(lemma, strength, date)")

def addlemma(words):
	parsed =ja_parser.parse(words)
	lemmas = []
	for token in parsed:
		if (not token.lemma_ in lemmas): #TODO probably needs to be fixed
			lemmas.append(token.lemma_)

	test = cur.execute("SELECT lemma FROM known").fetchall()
	for lemma in test:
		if (lemma[0] in lemmas):
			lemmas.remove(lemma[0])

	cur.executemany("INSERT INTO known VALUES (?, ?, ?)",[(lemma, 0, '1991-01-01') for lemma in lemmas])
	con.commit()

def updatelemma(lemma):
	cur.execute("UPDATE known SET date = ? WHERE lemma = ?",(datetime.date.today(),lemma))
	con.commit()

