import spacy, os

class parser:

	def __init__(self, model, auto=True):
		self.nlp = {}
		self.model = model
		self.auto = auto

	def parse(self, text, lang):
		self.load(lang)
		return([token for token in self.nlp[lang](text)])

	def explain(self, word):
		return spacy.explain(word)

	def sources(self, lang):
		self.load(lang)
		return self.nlp[lang].meta['sources']

	def vocab(self, word, lang):
		return word in self.nlp[lang].vocab

	def load(self, lang):
		if (not lang in self.nlp):
			try:
				self.nlp[lang] = spacy.load(self.model[lang])
			except:
				if self.auto:
					os.system(f"python -m spacy download {self.model[lang]}")
					self.nlp[lang] = spacy.load(self.model[lang])
				else:
					test = input(f"Pipeline {self.model[lang]} not found. Would you like to download it? (Y/N):")
					test = test.upper()
					if (test == "Y" or test == "YES"):
						os.system(f"python -m spacy download {self.model[lang]}")
						self.nlp[lang] = spacy.load(self.model[lang])