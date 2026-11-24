def count_upper(s):
	vowels = 'AEIOU'
	return sum(s[i] in vowels for i in range(0, len(s), 2))
