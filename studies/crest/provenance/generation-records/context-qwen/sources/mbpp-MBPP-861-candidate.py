
def anagram_lambda(texts, str1):
	return list(filter(lambda x: sorted(x) == sorted(str1), texts))
