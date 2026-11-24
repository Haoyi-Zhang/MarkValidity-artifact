def select_words(s, n):
	vowels = set("aeiouAEIOU")
	words = s.split()
	result = []
	for word in words:
		consonant_count = sum(bool(char.isalpha() and char not in vowels) for char in word)
		if consonant_count == n:
			list.append(result, word)
	return result
