from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_required, current_user
from . import db
from .database import *

config = current_app.config
logger = current_app.logger


targetlang = 'jpn'#TODO get rid of static values
nativelang = 'eng'

learn = Blueprint('learn', __name__)

@learn.route("/lemma/")
@login_required
def lemma():
	lemmas = getalllemmainfo(targetlang, current_user.id)
	return render_template("lemma.html", lemmas = lemmas)

@learn.route("/lemma/add/")
@login_required
def addinglemma():
	return render_template("addlemma.html")

@learn.route("/lemma/add/", methods=['POST'])
@login_required
def lemmaadded():
	words = request.form.get('words')
	lemmas = addlemma(words, targetlang, current_user.id)
	processsentencesjson(targetlang, current_user.id)
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
	senid = pickrandomsentence(targetlang,current_user.id)
	logger.info(f"Sentence id {senid}")
	text = gettext(senid, targetlang)
	audioids = getaudioids(senid)
	files = getaudiofiles(audioids)
	for i, file in enumerate(files, start=0):
		files[i] = url_for('static', filename='/audio/' + file)
	translation = getgoogle(senid, targetlang, nativelang)
	return render_template("work.html", text = text, audiofiles = files, translation=translation, senid=senid)

@learn.route('/work/', methods=["POST"])
@login_required
def workdone():
	senid = request.form.get("next")
	updatesentencelemma(senid, targetlang, current_user.id)
	marksentence(senid, targetlang, current_user.id)
	return redirect(url_for("learn.work"))