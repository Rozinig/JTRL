from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from .models import User
from . import db, mail
import json, datetime, random

config = current_app.config
logger = current_app.logger

auth = Blueprint('auth', __name__)

poslangs = config['LANGS']

@auth.route("/signup/")
def signup():
	langs ={}
	for lang in poslangs:
		if config['TARGET_LANG'][lang]:
			langs[lang]=poslangs[lang]
	return render_template("signup.html", langs=langs)

@auth.route('/signup/', methods=['POST'])
def signup_post():
	# code to validate and add user to database goes here
	email = request.form.get('email').lower()
	password = request.form.get('password')
	lang = request.form.get('lang')

	user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

	if user: # if a user is found, we want to redirect back to signup page so user can try again
		flash('Email address already exists')
		return redirect(url_for('auth.signup'))

	# create a new user with the form data. Hash the password so the plaintext version isn't saved.
	new_user = User(email=email, password=generate_password_hash(password, method='sha256'), emailauth=12345, 
		authdate='1991-01-01', currentlang=lang, settings=json.dumps({"tarlangs":[lang], "natlang":"eng"}))

	# add the new user to the database
	db.session.add(new_user)
	db.session.commit()
	flash("Account creation successful!")
	return redirect(url_for('auth.login'))

@auth.route("/login/" )
def login():
	return render_template("login.html")

@auth.route('/login', methods=['POST'])
def login_post():
	# login code goes here
	email = request.form.get('email').lower()
	password = request.form.get('password')
	remember = True if request.form.get('remember') else False

	user = User.query.filter_by(email=email).first()

	# check if the user actually exists
	# take the user-supplied password, hash it, and compare it to the hashed password in the database
	if not user or not check_password_hash(user.password, password):
		flash('Please check your login details and try again.')
		return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

	# if the above check passes, then we know the user has the right credentials
	login_user(user, remember=remember)
	return redirect(url_for('admin.home'))

@auth.route('/forgot')
def forgot():
	return render_template("forgotpassword.html")

@auth.route('/forgot', methods=['POST'])
def forgotpress():
	test = request.form.get("button")
	email = request.form.get("email").lower()
	user = User.query.filter_by(email=email).first()
	if (not user):
		flash("Email not found")
		return redirect(url_for('auth.forgot'))
		
	if (test == "email"):
		user.emailauth = random.randint(10000000, 99999999)
		user.authdate = datetime.date.today()
		db.session.commit()
		link = url_for('auth.forgot')
		mail.resetemail(email, user.emailauth, link, config['CONTACT_EMAIL'])
		flash("Email sent.")
		return render_template("forgotpassword.html", email=email)

	password = request.form.get("password")
	code = request.form.get("code")
	
	if (code == str(user.emailauth) and user.authdate == str(datetime.date.today())):
		user.password = generate_password_hash(password, method='sha256')
		flash("Password Reset")
		return redirect(url_for('auth.login'))
	flash("Code does not match.")
	return redirect(url_for('auth.forgot'))

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('admin.home'))