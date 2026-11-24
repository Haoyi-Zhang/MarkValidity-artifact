
def get_closest_vowel(word):
	length = len(word)
	vowels = "aeiouAEIOU"
    
	return next((word[i] for i in range(length - 2, 0, -1) if word[i] in vowels and word[i - 1] not in vowels and word[i + 1] not in vowels), "")
