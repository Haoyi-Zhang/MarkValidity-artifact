
def split_words(txt):
	if ' ' in txt:
		return txt.split()
	elif ',' in txt:
		return txt.split(',')
	else:
		return sum(bool(char.islower() and (ord(char) - ord('a')) % 2 == 1) for char in txt)
