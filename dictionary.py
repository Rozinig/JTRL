
import xml.etree.ElementTree as ET

jaDic = ET.parse('./ja_en/JMdict_e')
root = jaDic.getroot()

class definition:
	def __init__(self, num, kanjis, readings, meanings):
		self.id = num
		self.kanjis = kanjis
		self.readings = readings
		self.meanings = meanings

	def __str__(self):
		return(f"{self.id} {self.kanjis} {self.readings} {self.meanings}")


# returns information on a Japanese lemma. Returns only the used kanji but all readings and definitions
#TODO refine readings and definition to reduce information
def define(test):
	definitions=[]
	for entry in root:
		match = False
		kanjis = []
		readings = []
		meanings = []
		for child in entry:
			if (child.tag == "k_ele"):
				for ele in child:
					if (ele.text == test):
						match = True
						kanjis.append(ele.text)
			if (child.tag == "r_ele"):
				for ele in child:
					if (ele.tag == "reb"):
						readings.append(ele.text)
					if (ele.text == test):
						match = True
			if (match and child.tag == "sense"):
				for ele in child:
					if (ele.tag == "gloss"):
						meanings.append(ele.text)
		if (match):
			definitions.append(definition(entry[0].text,kanjis,readings,meanings))
	return(definitions)
