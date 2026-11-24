def start_withp(words):
	for phrase in words:
		word_list = phrase.split()
		p_words = [word for word in word_list if word.lower().startswith('p')]
		if 2 <= len(p_words):
			return (p_words[0], p_words[1])
	return None
