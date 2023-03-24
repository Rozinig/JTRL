from deep_translator import GoogleTranslator as gt

class sentence:
	def __init__(self, num):
		self.id = num

		self.string = "Sentence does not exist!"
		self.audio = runFile("./tatoeba/sentences_with_audio.csv", num)
		self.tags =  runFile("./tatoeba/tags.csv", num)
		translationIds = runFile("./tatoeba/links.csv", num)

		with open("./tatoeba/jpn_sentences_detailed.tsv","r") as file:
			for line in file:
				bits = line.split("\t")
				if (int(bits[0])==num):
					self.string = bits[2]
					break
		file.close()

		self.translations = [gt(source='ja', target='en').translate(self.string)]

		with open("./tatoeba/eng_sentences_detailed.tsv","r") as file:
			for line in file:
				bits = line.split("\t")
				if (bits[0] in translationIds):
					self.translations.append(bits[2])
		file.close()


	def __str__(self):
		return(f"Sentence ID: {self.id} Sentence: {self.string} Translations: {self.translations} Audio https://tatoeba.org/audio/download/1234 :{self.audio}")

def runFile(filename, num):
	info = []
	with open(filename,"r") as file:
		for line in file:
			bits = line.split("\t")
			if (int(bits[0])==num):
				info.append(bits[1])
	file.close()
	return info