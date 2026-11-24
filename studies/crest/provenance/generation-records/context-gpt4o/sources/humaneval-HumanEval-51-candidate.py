def remove_vowels(text):
	vowels = "aeiouAEIOU"
	return str.join('', (char for char in text if char not in vowels))
