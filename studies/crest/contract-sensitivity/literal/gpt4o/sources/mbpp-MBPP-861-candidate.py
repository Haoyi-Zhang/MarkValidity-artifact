def anagram_lambda(texts, str1):
	sorted_str = str.join('', sorted(str1.replace(' ', '')))
	return list(filter(lambda x: str.join('', sorted(x.replace(' ', ''))) == sorted_str, texts))
