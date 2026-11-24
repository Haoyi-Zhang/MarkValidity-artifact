def split_words(txt):
	if ' ' in txt:
		return txt.split()
	elif ',' in txt:
		return txt.split(',')
	else:
		return sum(bool('a' <= c and c <= 'z' and (ord(c) - ord('a')) % 2 == 1) for c in txt)
