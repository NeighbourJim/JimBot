from googletrans import Translator
t = Translator()

print(t.translate('salut! Mon nom est John.', src='auto', dest='en'))