from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import LoginManager, login_user, current_user
from . import db, mail

config = current_app.config
logger = current_app.logger

admin = Blueprint('admin', __name__)

@admin.route("/")
@admin.route("/home")
def home():
	if (current_user.is_authenticated):
		return render_template("userhome.html")
	else:
		return render_template("otherhome.html")

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