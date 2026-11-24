
def count_upper(s):
	uppercase_vowels = 'AEIOU'
	return sum((s[i] in uppercase_vowels for i in range(0, len(s), 2)))
