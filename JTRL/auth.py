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
	password2 = request.form.get('pass')
	lang = request.form.get('lang')

	if (password != password2):
		flash("Passwords don't match.")
		return redirect(url_for('auth.signup'))


	user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

	if user: # if a user is found, we want to redirect back to signup page so user can try again
		flash('Email address already exists. Try logging in.')
		return redirect(url_for('auth.signup'))

	# create a new user with the form data. Hash the password so the plaintext version isn't saved.
	new_user = User(email=email, password=generate_password_hash(password, method='sha256'), emailauth=12345, 
		authdate='1991-01-01', currentlang=lang, nativelang='eng', settings=json.dumps({"tarlangs":[lang],}), 
		streakdays=0, streakdate='1991-01-01', totalsentences=0, streakgoal = 10, streaknum = 0)

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

@auth.route('/change/', methods=['POST'])
@login_required
def change():
	button = request.form.get('button')
	if (button == "password"):
		password = request.form.get('ogpassword')
		if (check_password_hash(current_user.password, password)):
			password = request.form.get('password')
			password2 = request.form.get('pass')
			if (password != password2):
				flash("Passwords don't match.")
				return redirect(url_for('admin.settings'))
			current_user.password = generate_password_hash(password, method='sha256')
			db.session.commit()
			flash("Password Updated.")
			return redirect(url_for("admin.home"))
		else:
			flash("Incorrect Password.")
			return redirect(url_for("admin.settings"))
	if (button == "email"):
		email = request.form.get('email')
		user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
		if user: # if a user is found, we want to redirect back to signup page so user can try again
			flash('Email address already exists. Please use a different email.')
			return redirect(url_for('admin.settings'))
		current_user.email = email
		db.session.commit()
		flash(f"Email changed to {email}.")
		return redirect(url_for("admin.home"))

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('admin.home'))