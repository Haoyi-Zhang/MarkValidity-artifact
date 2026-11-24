def check(string):
	string = string.lower()
	vowels = set('aeiou')
	if set.issubset(vowels, set(string)):
		return 'accepted'
	return 'not accepted'
