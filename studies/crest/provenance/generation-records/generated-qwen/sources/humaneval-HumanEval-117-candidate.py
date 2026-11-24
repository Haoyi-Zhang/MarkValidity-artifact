
def select_words(s, n):
	words = s.split()
	result = []
	consonants = "bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ"
    
	for word in words:
		count = sum(char in consonants for char in word)
		if count == n:
			list.append(result, word)
    
	return result
