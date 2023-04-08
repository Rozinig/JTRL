import spacy

global nlp

nlp = {}

#TODO expand to all languages
#TODO download library if not already

def parse(text, lang):
	if (lang in nlp):
		pass
	elif (lang == 'jpn'):
		nlp['jpn'] = spacy.load("ja_core_news_sm") #ja_core_news_trf
	elif (lang == 'eng'):
		nlp['eng'] = spacy.load("en_core_web_sm") #en_core_web_trf
	return([token for token in nlp[lang](text)])

def explain(word):
	return spacy.explain(word)
