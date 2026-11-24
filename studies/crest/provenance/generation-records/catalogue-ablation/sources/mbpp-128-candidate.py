def long_words(n, str1):
	txt = str1.split(" ")
	word_len = []
	list.extend(word_len, (x for x in txt if len(x) > n))
	return word_len
