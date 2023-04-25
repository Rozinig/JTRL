import spacy

global nlp

nlp = {}

#TODO download library if not already

efficiency = {'cat':'ca_core_news_sm','cmn':'zh_core_web_sm','hrv':'hr_core_news_sm',
	'dan':'da_core_news_sm','nld':'nl_core_news_sm','eng':'en_core_web_sm',
	'fin':'fi_core_news_sm','fra':'fr_core_news_sm','deu':'de_core_news_sm',	
	'ell':'el_core_news_sm','ita':'it_core_news_sm','jpn':'ja_core_news_sm',
	'kor':'ko_core_news_sm','lit':'lt_core_news_sm','mkd':'mk_core_news_sm',
	'nob':'nb_core_news_sm','pol':'pl_core_news_sm','por':'pt_core_news_sm',
	'ron':'ro_core_news_sm','rus':'ru_core_news_sm','spa':'es_core_news_sm',
	'swe':'sv_core_news_sm','ukr':'uk_core_news_sm'}

accuracy = {'cat':'ca_core_news_trf', 'cmn':'zh_core_web_trf', 'hrv':'hr_core_news_lg',
'dan':'da_core_news_trf', 'nld':'nl_core_news_lg', 'eng':'en_core_web_trf',
'fin':'fi_core_news_lg', 'fra':'fr_dep_news_trf', 'deu':'de_dep_news_trf',
'ell':'el_core_news_lg', 'ita':'it_core_news_lg', 'jpn':'ja_core_news_trf',
'kor':'ko_core_news_lg', 'lit':'lt_core_news_lg', 'mkd':'mk_core_news_lg',
'nob':'nb_core_news_lg', 'pol':'pl_core_news_lg', 'por':'pt_core_news_lg',
'ron':'ro_core_news_lg', 'rus':'ru_core_news_lg', 'spa':'es_dep_news_trf',
'swe':'sv_core_news_lg', 'ukr':'uk_core_news_trf'}

def parse(text, lang):
	if (not lang in nlp):
		nlp[lang] = spacy.load(efficiency[lang]) #accuracy[lang])
	return([token for token in nlp[lang](text)])

def explain(word):
	return spacy.explain(word)