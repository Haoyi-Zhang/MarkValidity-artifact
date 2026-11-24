def long_words(n, str1):
	return [word for word in str1.split() if len(word) > n]
