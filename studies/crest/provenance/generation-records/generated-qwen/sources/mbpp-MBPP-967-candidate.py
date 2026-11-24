
def check(string):
	vowels = set("aeiouAEIOU")
	if set.issubset(vowels, set(string)):
		return 'accepted'
	return "not accepted"
