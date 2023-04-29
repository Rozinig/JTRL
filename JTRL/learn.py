from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_required, current_user
from . import db
from .database import *
import json

config = current_app.config
logger = current_app.logger

learn = Blueprint('learn', __name__)

@learn.route("/lemma/")
@login_required
def lemma():
	if touchuserdb(current_user.id, current_user.currentlang, f"{current_user.currentlang}_known_lemma"):
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
	processsentencesjson(current_user.currentlang, current_user.id)
	return render_template("lemmaadded.html", lemmas=lemmas)

@learn.route("/lemma/close/")
@login_required
def closelemma():
	return render_template("closelemma.html")

@learn.route("/grammar/")
@login_required
def grammar():
	return render_template("grammar.html")

@learn.route("/work/")
@login_required
def work():
	if not touchuserdb(current_user.id, current_user.currentlang, f"{current_user.currentlang}_available_sentences"):
		flash("You don't have any sentences available. Try adding more words.")
		return redirect(url_for("learn.addinglemma"))
	senid = pickrandomsentence(current_user.currentlang,current_user.id)
	logger.info(f"Sentence id {senid}")
	text = gettext(senid, current_user.currentlang)
	audioids = getaudioids(senid)
	files = getaudiofiles(audioids)
	for i, file in enumerate(files, start=0):
		files[i] = url_for('static', filename='/audio/' + file)
	translation = getgoogle(senid, current_user.currentlang, getnativelang())
	return render_template("work.html", text = text, audiofiles = files, translation=translation, senid=senid)

@learn.route('/work/', methods=["POST"])
@login_required
def workdone():
	senid = request.form.get("next")
	updatesentencelemma(senid, current_user.currentlang, current_user.id)
	marksentence(senid, current_user.currentlang, current_user.id)
	return redirect(url_for("learn.work"))

def getnativelang():
	print(current_user.settings)
	info = json.loads(current_user.settings)
	return info['natlang']