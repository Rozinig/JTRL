from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from database import *
import mail
import time
import json
import os

db = SQLAlchemy()
app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
db.init_app(app)

targetlang = 'jpn'#TODO get rid of static values
user = 'william'
nativelang = 'eng'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(UserMixin, db.Model): #UserMixin, 
	id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
	email = db.Column(db.String(100), unique=True)
	password = db.Column(db.String(100))
	emailauth = db.Column(db.Integer)
	authdate = db.Column(db.String(100))
#if (os.path.isfile('./instance/auth.db')):
with app.app_context():
	db.create_all()

loglevel = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40}
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(loglevel[app.config["STREAM_LOG_LEVEL"]])
ch.setFormatter(formatter)

fh = logging.FileHandler('./logs/main.log')
fh.setLevel(loglevel[app.config['FILE_LOG_LEVEL']])
fh.setFormatter(formatter)

minlevel = min(loglevel[app.config['FILE_LOG_LEVEL']], loglevel[app.config['STREAM_LOG_LEVEL']])
logger = app.logger
logger.setLevel(minlevel)
logger.addHandler(ch)
logger.addHandler(fh)

databaselogger = logging.getLogger('database')
databaselogger.addHandler(ch)
databaselogger.addHandler(fh)

#Build/Rebuild Databases
nativelangs = app.config['NATIVE_LANG']
targetlangs = app.config['TARGET_LANG']

if (app.config['FORCE_REBUILT']):
	test = input("Config file is set to force rebuilt. Are you sure you want to contiune? (Y/N):")
	test = test.upper()
	if (test != "Y" and test != "YES"):
		app.config['FORCE_REBUILT'] = False


for lang in nativelangs:
	dbexists = os.path.isfile(f'./lang/{lang}.db')
	if ((not dbexists or app.config['FORCE_REBUILT']) and (nativelangs[lang] or targetlangs[lang])):
		app.logger.info(f"Rebuilding {lang} database. This might take a while...")
		t = time.time()
		loadlang(targetlang)
		app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild {lang} database")

	if ((not dbexists or app.config['FORCE_REBUILT']) and targetlangs[lang]):
		app.logger.info(f"Rebuilding {lang} json database. This might take a while...")
		t = time.time()
		processlangjson(lang)
		app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild {lang} json database")


if (not os.path.exists('./lang/all_lang.db')):
	t = time.time()
	app.logger.info("Rebuilding all_lang database. This might take a while...")
	#loadaux('tags')
	loadaux('links')
	loadaux('sentences_with_audio') #need to exclude Create commons
	app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild all_lang database")


langs = {'cat','Catalan', 'cmn','Chinese (mandarin i think)', 'hrv','Croatian',
'dan','Danish', 'nld','Dutch', 'eng','English', 'fin','Finnish', 'fra','French', 'deu','German',
'ell','Greek', 'ita','Italian', 'jpn','Japanese', 'kor','Korean', 'lit','Lithuanian', 'mkd','Macedonian',
'nob','Norwegian Bokmal', 'pol','Polish', 'por','Portuguese', 'ron','Romanian', 'rus','Russian', 'spa','Spanish',
'swe','Swedish', 'ukr','Ukrainian'}




@app.route("/")
@app.route("/home")
def home():
	if (current_user.is_authenticated):
		return render_template("userhome.html")
	else:
		return render_template("otherhome.html")

@app.route("/about/")
def about():
	return render_template("about.html")

@app.route("/lemma/")
@login_required
def lemma():
	lemmas = getalllemmainfo(targetlang, current_user.id)
	return render_template("lemma.html", lemmas = lemmas)

@app.route("/lemma/add/")
@login_required
def addinglemma():
	return render_template("addlemma.html")

@app.route("/lemma/add/", methods=['POST'])
@login_required
def lemmaadded():
	words = request.form.get('words')
	lemmas = addlemma(words, targetlang, current_user.id)
	processsentencesjson(targetlang, current_user.id)
	return render_template("lemmaadded.html", lemmas=lemmas)

@app.route("/lemma/close/")
@login_required
def closelemma():
	return render_template("closelemma.html")

@app.route("/grammar/")
@login_required
def grammar():
	return render_template("grammar.html")

@app.route("/work/")
@login_required
def work():
	senid = pickrandomsentence(targetlang,current_user.id)
	app.logger.info(f"Sentence id {senid}")
	text = gettext(senid, targetlang)
	audioids = getaudioids(senid)
	files = getaudiofiles(audioids)
	for i, file in enumerate(files, start=0):
		files[i] = url_for('static', filename='/audio/' + file)
	translation = getgoogle(senid, targetlang, nativelang)
	return render_template("work.html", text = text, audiofiles = files, translation=translation, senid=senid)

@app.route('/work/', methods=["POST"])
@login_required
def workdone():
	senid = request.form.get("next")
	updatesentencelemma(senid, targetlang, current_user.id)
	marksentence(senid, targetlang, current_user.id)
	return redirect(url_for("work"))

@app.route("/contact/")
def contact():
	email = ""
	if (current_user.is_authenticated):
		email = current_user.email
	return render_template("contact.html", email=email)

@app.route("/contact/", methods=['POST'])
def contacted():
	name = request.form.get('name')
	email = request.form.get('email')
	message = request.form.get('message')
	if (False): #TODO check email is email
		flash('Pease fillout all fields.')
		return redirect(url_for('contact'))
	if (not name or not message):
		flash('Pease fillout all fields.')
		return redirect(url_for('contact'))
	mail.contactemail(email, name, message, app.config['CONTACT_EMAIL'])
	app.logger.info(f" User {name} sent a message from {email}: {message}")
	return render_template("contacted.html", name=name)

@app.route("/signup/")
def signup():
	return render_template("signup.html")

@app.route('/signup/', methods=['POST'])
def signup_post():
	# code to validate and add user to database goes here
	email = request.form.get('email')
	password = request.form.get('password')

	user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

	if user: # if a user is found, we want to redirect back to signup page so user can try again
		flash('Email address already exists')
		return redirect(url_for('signup'))

	# create a new user with the form data. Hash the password so the plaintext version isn't saved.
	new_user = User(email=email, password=generate_password_hash(password, method='sha256'), emailauth=12345, authdate='1991-01-01')

	# add the new user to the database
	db.session.add(new_user)
	db.session.commit()

	return redirect(url_for('login'))

@app.route("/login/" )
def login():
	return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_post():
	# login code goes here
	email = request.form.get('email')
	password = request.form.get('password')
	remember = True if request.form.get('remember') else False

	user = User.query.filter_by(email=email).first()

	# check if the user actually exists
	# take the user-supplied password, hash it, and compare it to the hashed password in the database
	if not user or not check_password_hash(user.password, password):
		flash('Please check your login details and try again.')
		return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

	# if the above check passes, then we know the user has the right credentials
	login_user(user, remember=remember)
	return redirect(url_for('home'))

'''@app.route("/<other>/")
def other(other):
	other=escape(other)
	return #redirect'''

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('home'))

if (__name__=='__main__'):
	app.run(debug=True)

