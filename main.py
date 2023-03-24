import ja_parser
#import en_parser
import dictionary
import sentence
import known

#enText = "The other day, I built a bridge."
#print(en_parser.parse(enText), '\n')

test = "私は眠らなければなりません。"
known.addlemma(test)
known.updatelemma("私")


jaText = sentence.sentence(4703)
print(jaText.string)
print(jaText.translations)

thing = ja_parser.parse(jaText.string)
for x in thing:
	print(f"{x.text}, {x.lemma_}, {x.pos_}, {x.tag_}, {x.dep_}")

test = dictionary.define(thing[0].text)

for things in test:
	print(things)

