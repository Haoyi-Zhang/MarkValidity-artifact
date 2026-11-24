
def words_ae(text):
	return [word for word in text.split() if word.startswith(('a', 'e'))]
