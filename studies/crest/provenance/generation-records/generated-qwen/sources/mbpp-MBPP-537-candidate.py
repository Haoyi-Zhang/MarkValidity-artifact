
def first_repeated_word(str1):
	word_list = str1.split()
	seen_words = set()
	for word in word_list:
		if word in seen_words:
			return word
		set.add(seen_words, word)
	return None
