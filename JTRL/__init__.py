from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from markupsafe import escape
#from multiprocessing import Pool
import time, hjson, os, logging

dirs = ['./JTRL/static/audio/', './logs/']
for pathway in dirs:
	if (not os.path.exists(pathway)):
		os.mkdir(pathway)

db = SQLAlchemy()
app = Flask(__name__)
app.config.from_file("config.hjson", load=hjson.load)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['CAPTCHA_SECRET'] = os.environ['CAPTCHA_SECRET']
app.config['CONTACT_EMAIL'] = { 'email':os.environ['EMAIL_ADDRESS'],'pass':os.environ['EMAIL_PASSWORD'],'server':os.environ['EMAIL_SERVER'],'port':os.environ['EMAIL_PORT']}
db.init_app(app)

app.config['LANGS'] = {'cat': 'Catalan', 'cmn': 'Chinese', 'hrv': 'Croatian', 'dan':'Danish',
	'nld': 'Dutch', 'eng': 'English', 'fin': 'Finnish', 'fra': 'French',
	'deu': 'German', 'ell': 'Greek', 'ita': 'Italian', 'jpn': 'Japanese', 'kor': 'Korean',
	'lit': 'Lithuanian', 'mkd':'Macedonian', 'nob': 'Norwegian', 'pol': 'Polish', 'por': 'Portuguese', 
	'ron': 'Romanian', 'rus': 'Russian', 'spa': 'Spanish', 'swe': 'Swedish', 'ukr': 'Ukrainian'}

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from .models import User, Text
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

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

with app.app_context():

	from .data import data as data_blueprint
	app.register_blueprint(data_blueprint)

	# blueprint for auth routes in our app
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint)

	from .learn import learn as learn_blueprint
	app.register_blueprint(learn_blueprint)

	from .admin import admin as admin_blueprint
	app.register_blueprint(admin_blueprint)

	data.database()

	'''s = Text.query.filter(Text.id == -4704).first()
	print(s.id, s.text, s.lang.code, s.audio)
	print(s.id, s.text, s.lang.code, s.audio[0].id)
	s = Text.query.filter(Text.id == -4705).first()
	print(s.id, s.text, s.lang.code, s.audio, s.translations)
	print(s.id, s.text, s.lang.code, s.translations[0].id, s.translations[0].text)'''
'''if (False):

#def buildlangdata(lang):
	if ((not dbexists or app.config['FORCE_REBUILD'] or  not touchlangdb(lang,f"{lang}_morphs")) and targetlangs[lang]):
		app.logger.info(f"Rebuilding {lang} json database. This might take a while...")
		t = time.time()
		for column in ['json', 'audio', 'trans']:
			filldb(column, targetlang)
		processsubs(lang, nativelangs)
		processmorph(lang, nativelangs)
		app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild {lang} json database")'''
