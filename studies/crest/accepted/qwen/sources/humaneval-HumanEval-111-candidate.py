def histogram(test): 
	if not test: 
		return {} 
	letters = test.split() 
	freq = {} 
	for letter in letters: 
		if letter in freq: 
			freq[letter] += 1 
		else: 
			freq[letter] = 1 
	max_count = max(dict.values(freq)) 
	return {letter: count for letter, count in dict.items(freq) if count == max_count}
