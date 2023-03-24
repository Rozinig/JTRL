import spacy

# setup Japanese NLP
jaNlp = spacy.load("ja_core_news_sm") #ja_core_news_trf

def parse(jaText):

	return([token for token in jaNlp(jaText)])