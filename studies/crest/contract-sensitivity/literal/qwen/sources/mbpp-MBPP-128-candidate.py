
def long_words(n, str1):
	words = str1.split()
	return [word for word in words if len(word) > n]
