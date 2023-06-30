from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_required, current_user
from deep_translator import GoogleTranslator as gt
from . import db
import json, datetime, time

config = current_app.config
logger = current_app.logger

learn = Blueprint('learn', __name__)
from . import data

@learn.route("/lemma/")
@login_required
def lemma():
	lemmas = data.getknownlemma(current_user)
	if len(lemmas):
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
	lemmas, newgrammar, notlemma = data.addlemmagrammar(words, current_user)
	print(notlemma)
	grammar = data.pullusergrammar(current_user)
	return render_template("lemmaadded.html", lemmas=lemmas, newgrammar=newgrammar, grammar=grammar, notlemma=notlemma)

@learn.route("/lemma/close/")
@login_required
def closelemma():
	return render_template("closelemma.html")

@learn.route("/grammar/")
@login_required
def grammar():
	grammar = data.pullusergrammar(current_user)
	return render_template("grammar.html", grammar=grammar)

@learn.route("/grammar/", methods=["POST"])
@login_required
def grammarchange():
	grammar = request.form.get('button')
	grammar = json.loads(grammar.replace("'", '"').replace('True','1').replace('False','0'))
	for gtype in grammar:
		for thing in grammar[gtype]:
			for know in grammar[gtype][thing]:
				if request.form.get(f'{gtype}_{thing}_{know}') == 'on': 
					grammar[gtype][thing][know] = True 
				else: 
					grammar[gtype][thing][know] = False
	data.pushusergrammar(current_user, grammar)
	flash("Grammar changes Saved.")
	return redirect(url_for("admin.home"))

@learn.route("/work/")
@login_required
def work():
	t = time.time()
	text = data.nexttext(current_user)
	if not text:
		flash("You don't have any sentences available. Try adding more words or grammar.")
		return redirect(url_for("learn.addinglemma"))

	info = data.additionalinfo(text)
	files = data.getaudiofiles(text)
	for i, file in enumerate(files, start=0):
			files[i] = url_for('static', filename='/audio/' + file)
	translations = []
	for trans in text.translations:
		if trans.lang == current_user.currentlang:
			translations.append(trans.text)
	if not len(translations):
		translations.append(gt(source=config['TRANS_CODE'][current_user.currentlang_code], 
		target=config['TRANS_CODE'][current_user.nativelang_code]).translate(text.text))
	if (current_user.streakdate == datetime.date.today()):
		streakcount = False
	else:
		streakcount = True
	logger.info(f"total sentence load time was {time.time()-t}")
	return render_template("work.html", text = text.text, audiofiles = files, 
		translations=translations, senid=text.id, info=info, streakcount=streakcount)

@learn.route('/work/', methods=["POST"])
@login_required
def workdone():
	if (current_user.streakdate == datetime.date.today()):
		pass
	elif (current_user.streakdate == datetime.date.today()-datetime.timedelta(days=1)):
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
	textid = request.form.get("next")
	data.recordtext(current_user, textid)
	return redirect(url_for("learn.work"))