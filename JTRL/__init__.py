from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from markupsafe import escape
import time, json, os
from .database import *

db = SQLAlchemy()
app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
db.init_app(app)

app.config['LANGS'] = {'cat': 'Catalan', 'cmn': 'Chinese', 'hrv': 'Croatian', 'dan':'Danish',
	'nld': 'Dutch', 'eng': 'English', 'fin': 'Finnish', 'fra': 'French',
	'deu': 'German', 'ell': 'Greek', 'ita': 'Italian', 'jpn': 'Japanese', 'kor': 'Korean',
	'lit': 'Lithuanian', 'mkd':'Macedonian', 'nob': 'Norwegian', 'pol': 'Polish', 'por': 'Portuguese', 
	'ron': 'Romanian', 'rus': 'Russian', 'spa': 'Spanish', 'swe': 'Swedish', 'ukr': 'Ukrainian'}

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


from .models import User
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


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
		loadlang(lang)
		app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild {lang} database")

	if ((not dbexists or app.config['FORCE_REBUILT'] or  not touchlangdb(lang,f"{lang}_json")) and targetlangs[lang]):
		app.logger.info(f"Rebuilding {lang} json database. This might take a while...")
		t = time.time()
		processlangjson(lang)
		processsubsjson(lang, [nativelang])
		processmorphjson(targetlang, [nativelang])
		app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild {lang} json database")


if (not os.path.exists('./lang/all_lang.db')):
	t = time.time()
	app.logger.info("Rebuilding all_lang database. This might take a while...")
	#loadaux('tags')
	loadaux('links')
	loadaux('sentences_with_audio') #need to exclude Create commons
	app.logger.info(f"It took {(time.time()-t)/60} minutes to rebuild all_lang database")


with app.app_context():
	# blueprint for auth routes in our app
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint)

	from .learn import learn as learn_blueprint
	app.register_blueprint(learn_blueprint)

	from .admin import admin as admin_blueprint
	app.register_blueprint(admin_blueprint)



#if (__name__=='__main__'):
#	app.run(debug=True)

