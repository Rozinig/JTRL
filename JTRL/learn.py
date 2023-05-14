from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_required, current_user
from . import db
from .database import *
import json, datetime

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
	lemmas = addlemma(words, current_user.currentlang, current_user.id)
	newgrammar = pullgrammar(words, current_user.currentlang)
	grammar = pullusergram(current_user.currentlang, current_user.id)
	return render_template("lemmaadded.html", lemmas=lemmas, newgrammar=newgrammar, grammar=grammar)

@learn.route("/lemma/close/")
@login_required
def closelemma():
	return render_template("closelemma.html")

@learn.route("/grammar/")
@login_required
def grammar():
	grammar = pullusergram(current_user.currentlang, current_user.id)
	return render_template("grammar.html", grammar=grammar)

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
	if not touchuserdb(current_user.currentlang, current_user.id, f"{current_user.currentlang}_available_sentences"):
		flash("You don't have any sentences available. Try adding more words.")
		return redirect(url_for("learn.addinglemma"))
	senid = pickrandomsentence(current_user.currentlang,current_user.id)
	logger.info(f"Sentence id {senid}")
	text = gettext(senid, current_user.currentlang)
	audioids = getaudioids(senid)
	files = getaudiofiles(audioids)
	for i, file in enumerate(files, start=0):
		files[i] = url_for('static', filename='/audio/' + file)
	info = additionalinfo(current_user.currentlang, senid)
	translation = getgoogle(senid, current_user.currentlang, current_user.nativelang)
	if (current_user.streakdate == str(datetime.date.today())):
		streakcount = False
	else:
		streakcount = True

	return render_template("work.html", text = text, audiofiles = files, translation=translation, senid=senid, info=info)

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
	processsentencesjson(current_user.currentlang, current_user.id)
	flash("Sentences Updated.")
	return redirect(url_for("admin.home"))