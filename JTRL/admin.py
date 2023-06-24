from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_user, current_user, login_required
from . import db, mail
from .models import Lang
import json

config = current_app.config
logger = current_app.logger

admin = Blueprint('admin', __name__)
from . import data

@admin.route("/")
@admin.route("/home")
def home():
	if (current_user.is_authenticated):
		currentlangs = current_user.targetlangs
		langs ={}
		for lang in currentlangs:
			if lang != current_user.currentlang:
				langs[lang.code]=config['LANGS'][lang.code]
		return render_template("userhome.html", langs=langs, lenlangs=len(langs))
	else:
		return render_template("otherhome.html")

@admin.route("/")
@admin.route("/home", methods=['POST'])
def homeupdate():
	if (current_user.is_authenticated):
		button = request.form.get('button')
		if (button == "switch"):
			lang = request.form.get('lang')
			current_user.currentlang_code = lang
			db.session.commit()		
	return redirect(url_for("admin.home"))


@admin.route("/about/")
def about():
	return render_template("about.html")

@admin.route("/contact/")
def contact():
	email = ""
	if (current_user.is_authenticated):
		email = current_user.email
	return render_template("contact.html", email=email)

@admin.route("/contact/", methods=['POST'])
def contacted():
	name = request.form.get('name')
	email = request.form.get('email').lower()
	message = request.form.get('message')
	if (False): #TODO check email is email -- already kind of done in html
		flash('Pleae enter a vaild email')
		return redirect(url_for('admin.contact'))
	if (not name or not message):
		flash('Pease fillout all fields.')
		return redirect(url_for('admin.contact'))
	mail.contactemail(email, name, message, config['CONTACT_EMAIL'])
	logger.info(f" User {name} sent a message from {email}: {message}")
	return render_template("contacted.html", name=name)

@admin.route("/settings/")
@login_required
def settings():
	currentlangs = current_user.targetlangs
	alangs ={}
	rlangs = {}
	nlangs = {}
	currentlangs = [lang.code for lang in currentlangs]
	for lang in config['LANGS']:
		if config['TARGET_LANG'][lang] and not lang in currentlangs:
			alangs[lang]=config['LANGS'][lang]
		if lang in currentlangs:
			rlangs[lang]=config['LANGS'][lang]
		if config['NATIVE_LANG'][lang] and not lang == current_user.nativelang_code:
			nlangs[lang]=config['LANGS'][lang]

	return render_template("settings.html", alangs=alangs, lenalangs=len(alangs), rlangs=rlangs, lenrlangs=len(rlangs),
		streakgoal=current_user.streakgoal, nlangs=nlangs, lennlangs=len(nlangs), nativelang=config['LANGS'][current_user.nativelang_code])

@admin.route("/settings/", methods=['POST'])
@login_required
def updatesettings():
	button = request.form.get('button')
	if (button == "addlang"):
		lang = request.form.get('lang')
		lang = Lang.query.filter(Lang.code == lang).first()
		current_user.targetlangs.append(lang)
		current_user.currentlang = lang
		db.session.commit()
		data.pushusergrammar(current_user, data.pullusergrammar(current_user))
		flash(f"{config['LANGS'][lang.code]} added.")
		return redirect(url_for("admin.home"))
	if (button == "removelang"):
		lang = request.form.get('lang')
		lang = Lang.query.filter(Lang.code == lang).first()
		if len(current_user.targetlangs) == 1:
			flash("You can't remove your only language.")
			return redirect(url_for("admin.home"))
		current_user.targetlangs.remove(lang)
		current_user.currentlang = current_user.targetlangs[0]
		db.session.commit()
		flash(f"{config['LANGS'][lang.code]} removed.")
		return redirect(url_for("admin.home"))
	if (button == "goal"):
		goal = request.form.get('goal')
		current_user.streakgoal = goal
		db.session.commit()
		flash(f"Streak goal set to {goal}.")
		return redirect(url_for("admin.home"))
	if (button == "nativelang"):
		lang = request.form.get('lang')
		current_user.nativelang_code = lang
		db.session.commit()
		flash(f"Your native language has been changed to {config['LANGS'][current_user.nativelang_code]}.")
		return redirect(url_for("admin.home"))

	flash("There was an error updating settings.")
	return redirect(url_for("admin.home"))