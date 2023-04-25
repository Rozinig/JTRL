# JTRL
The intent of this program is to download a data base of sentences in a language that you are trying to learn from Tatoeba and then create a condensed list of those sentence which only contains words and grammar that you know.


A program to help give you just the right language learning practice material.
JTRL stands for Just the right level.
The idea is that a large group of language content is processed into a database and then 
only the parts of it that meet your level are displayed to you for practice.

To start Vitural Enviroment
source .env/bin/activate


to start program with flask
flask --app main run

Layout

JTRL
|-Database
| |-Corpus
| | |-Parser
| | |-Translation
| |-Vocab
| | |-List   https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project
| | |-Profiencty
| |-Grammar
| | |-Lessons
| | |-Profiencty
|-UI
| |-Alphabet
| |-Words
| |-Sentences
| |-Paragraphs
| |-Listening mode
|-Algorithem
| |-SRS
| |-Choose from corpus
|
|

Tatoeba Corpus

	english sentences and japanese sentences 
	
	sentences with audio	Contains the ids of the sentences, in all languages, for which audio is available. Other fields indicate who recorded the audio, its license and a URL to attribute the author. If the license field is empty, you may not reuse the audio outside the Tatoeba project. A single sentence can have one or more audio, each from a different voice. To download a particular audio, use its audio id to compute the download URL. For example, to download the audio with the id 1234, the URL is https://tatoeba.org/audio/download/1234. 
	
	links			Contains the links between the sentences. 1 [tab] 77 means that sentence #77 is the translation of sentence #1. The reciprocal link is also present, so the file will also contain a line that says 77 [tab] 1. 
	
	sentences		Contains all the sentences in the selected language. Each sentence is associated with a unique id and an ISO 639-3 language code. 
	
	sentences base		Each sentence is listed as original or a translation of another. The "base" field can have the following values:
    zero: The sentence is original, not a translation of another.
    greater than zero: The id of the sentence from which it was translated.
    \N: Unknown (rare).
    
    	tags			tag for each sentence
    	



https://spacy.io/usage
https://pypi.org/project/deep-translator/
https://www.olivieraubert.net/vlc/python-ctypes/doc/index.html  for vlc
https://www.tutorialspoint.com/flask/flask_application.htm
https://tatoeba.org/en/downloads
Rebuild virtual Environment

python -m venv .env
source .env/bin/activate
pip install -U pip setuptools wheel
pip install -U spacy
python -m spacy download en_core_web_sm		
python -m spacy download ja_core_news_sm
pip install -U deep-translator
pip install wget
pip install python-vlc
pip install Flask flask-login flask_sqlalchemy



replace with when moving to high accuracy:
python -m spacy download en_core_web_trf
python -m spacy download ja_core_news_trf



pages
	home
		if logged in show options to move to other pages
		if not logged in show login box/signup box and introduction information
	login
		login page
	signup
		sign up page
	about
		basic info about the website
	lemma
		view all known lemma
		option to remove lemma
	lemma/add
		textbox to add lemma
	lemma/close
		show all close lemma
	grammar
		show list of grammar with checkboxes to allow each into list
	work page
		shows audio files
		shows target language text
		hidden native language text until shown

User auth
	id, email, password, email *un*authentied
User info
	id, Join date, last login, list of target langs number of sentences, pateron api key
User Settings
	id, nativelang, list of target langs True false,  , darkmode, blob

git status
git add stuff
git commit -m "stuff"
git push origin master