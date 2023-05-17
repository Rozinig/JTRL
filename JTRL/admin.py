from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_user, current_user, login_required
from . import db, mail
import json

config = current_app.config
logger = current_app.logger

admin = Blueprint('admin', __name__)

@admin.route("/")
@admin.route("/home")
def home():
	if (current_user.is_authenticated):
		currentlangs = json.loads(current_user.settings)["tarlangs"]
		langs ={}
		for lang in currentlangs:
			if lang != current_user.currentlang:
				langs[lang]=config['LANGS'][lang]
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
			current_user.currentlang = lang
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
	currentlangs = json.loads(current_user.settings)["tarlangs"]
	alangs ={}
	rlangs = {}
	nlangs = {}
	for lang in config['LANGS']:
		if config['TARGET_LANG'][lang] and not lang in currentlangs:
			alangs[lang]=config['LANGS'][lang]
		if lang in currentlangs:
			rlangs[lang]=config['LANGS'][lang]
		if config['NATIVE_LANG'][lang] and not lang == current_user.nativelang:
			nlangs[lang]=config['LANGS'][lang]

	return render_template("settings.html", alangs=alangs, lenalangs=len(alangs), rlangs=rlangs, lenrlangs=len(rlangs),
		streakgoal=current_user.streakgoal, nlangs=nlangs, lennlangs=len(nlangs), nativelang=config['LANGS'][current_user.nativelang])

@admin.route("/settings/", methods=['POST'])
@login_required
def updatesettings():
	button = request.form.get('button')
	if (button == "addlang"):
		lang = request.form.get('lang')
		currentsettings = json.loads(current_user.settings)
		currentsettings['tarlangs'].append(lang)
		current_user.settings=json.dumps(currentsettings)
		current_user.currentlang = lang
		db.session.commit()
		flash(f"{config['LANGS'][lang]} added.")
		return redirect(url_for("admin.home"))
	if (button == "removelang"):
		lang = request.form.get('lang')
		currentsettings = json.loads(current_user.settings)
		if len(currentsettings['tarlangs']) == 1:
			flash("You can't remove your only language.")
			return redirect(url_for("admin.home"))
		currentsettings['tarlangs'].remove(lang)
		current_user.settings=json.dumps(currentsettings)
		current_user.currentlang = currentsettings['tarlangs'][0]
		db.session.commit()
		flash(f"{config['LANGS'][lang]} removed.")
		return redirect(url_for("admin.home"))
	if (button == "goal"):
		goal = request.form.get('goal')
		current_user.streakgoal = goal
		db.session.commit()
		flash(f"Streak goal set to {goal}.")
		return redirect(url_for("admin.home"))
	if (button == "nativelang"):
		lang = request.form.get('lang')
		current_user.nativelang = lang
		db.session.commit()
		flash(f"Your native language has been changed to {config['LANGS'][current_user.nativelang]}.")
		return redirect(url_for("admin.home"))

	flash("There was an error updating settings.")
	return redirect(url_for("admin.home"))