from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_required, current_user
from . import db
from .database import *
import json, datetime, time

config = current_app.config
logger = current_app.logger

learn = Blueprint('learn', __name__)

@learn.route("/lemma/")
@login_required
def lemma():
	if touchuserdb(current_user.currentlang, current_user.id, f"{current_user.currentlang}_known_lemma"):
		lemmas = getalllemmainfo(current_user.currentlang, current_user.id)
		return render_template("lemma.html", lemmas = lemmas)
	flash("You don't have any known words.")
	return redirect(url_for("learn.addinglemma"))


@learn.route("/lemma/add/")
@login_required
def addinglemma():
	return render_template("addlemma.html")

@learn.route("/lemma/add/", methods=['POST'])
@login_required
def lemmaadded():
	words = request.form.get('words')
	lemmas, newgrammar = addlemmagrammar(words, current_user.currentlang, current_user.id)
	grammar = pullusergram(current_user.currentlang, current_user.id)
	grammarinfo = pullgrammartrans(current_user.currentlang)
	return render_template("lemmaadded.html", lemmas=lemmas, newgrammar=newgrammar, grammar=grammar, grammarinfo=grammarinfo)

@learn.route("/lemma/close/")
@login_required
def closelemma():
	return render_template("closelemma.html")

@learn.route("/grammar/")
@login_required
def grammar():
	grammar = pullusergram(current_user.currentlang, current_user.id)
	grammarinfo = pullgrammartrans(current_user.currentlang)
	return render_template("grammar.html", grammar=grammar, grammarinfo=grammarinfo)

@learn.route("/grammar/", methods=["POST"])
@login_required
def grammarchange():
	grammar = request.form.get('button')
	grammar = json.loads(grammar.replace("'", '"'))
	for gtype in grammar:
		for thing in grammar[gtype]:
			for know in grammar[gtype][thing]:
				if request.form.get(f'{gtype}_{thing}_{know}') == 'on': 
					grammar[gtype][thing][know] = True 
				else: 
					grammar[gtype][thing][know] = False
	pushusergram(current_user.currentlang, current_user.id, grammar)
	flash("Grammar changes Saved.")
	return redirect(url_for("admin.home"))

@learn.route("/work/")
@login_required
def work():
	t = time.time()
	if not touchuserdb(current_user.currentlang, current_user.id, f"{current_user.currentlang}_available_sentences"):
		flash("You don't have any sentences available. Try adding more words.")
		return redirect(url_for("learn.addinglemma"))

	sentence = picksentence(current_user.currentlang,current_user.id)
	info = additionalinfo(current_user.currentlang, sentence)
	files = []
	for i, file in enumerate(json.loads(sentence['audio']), start=0):
		files[i] = url_for('static', filename='/audio/' + file)
	translation = getgoogle(sentence['text'], current_user.currentlang, current_user.nativelang)
	if (sentence['trans'] != None):
		trans = getlations(json.loads(sentence['trans']), current_user.nativelang)
	if (current_user.streakdate == str(datetime.date.today())):
		streakcount = False
	else:
		streakcount = True
	logger.info(f"total sentence load time was {time.time()-t}")
	return render_template("work.html", text = sentence['text'], audiofiles = files, translation=translation, senid=sentence['id'], info=info, streakcount=streakcount)

@learn.route('/work/', methods=["POST"])
@login_required
def workdone():
	if (current_user.streakdate == str(datetime.date.today())):
		pass
	elif (current_user.streakdate == str(datetime.date.today()-datetime.timedelta(days=1))):
		current_user.streaknum += 1
		if (current_user.streaknum >= current_user.streakgoal):
			current_user.streakdays += 1
			current_user.streaknum = 0
			current_user.streakdate = datetime.date.today()
			flash("Congadulations you hit your goal for today!")
	else:
		current_user.streakdays = 0
		current_user.streaknum = 1
		current_user.streakdate = datetime.date.today()-datetime.timedelta(days=1)
	current_user.totalsentences += 1
	db.session.commit()
	senid = request.form.get("next")
	updatesentencelemma(senid, current_user.currentlang, current_user.id)
	marksentence(senid, current_user.currentlang, current_user.id)
	return redirect(url_for("learn.work"))

@learn.route('/updating/')
@login_required
def updatesentences():
	processsentences(current_user.currentlang, current_user.id)
	flash("Sentences Updated.")
	return redirect(url_for("admin.home"))