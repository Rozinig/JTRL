import spacy

#setup english NLP
ennlp = spacy.load("en_core_web_sm") #en_core_web_trf

def parse(enText):
	return([(w.text, w.pos_) for w in ennlp(enText)])