def anti_shuffle(s):
	def sort_chars(word):
		return str.join('', sorted(word))
    
	words = s.split(' ')
	sorted_words = [sort_chars(word) for word in words]
	return str.join(' ', sorted_words)
