def first_repeated_word(str1):
	words = str1.split()
	seen = set()
	for word in words:
		if word in seen:
			return word
		set.add(seen, word)
	return None
