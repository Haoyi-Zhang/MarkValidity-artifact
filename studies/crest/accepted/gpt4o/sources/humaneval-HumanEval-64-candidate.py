def vowels_count(s):
	s = s.lower()
	vowels = 'aeiou'
	count = sum(char in vowels for char in s)
	if s.endswith('y'):
		count += 1
	return count


assert vowels_count("abcde") == 2
assert vowels_count("ACEDY") == 3
assert vowels_count("hello") == 2
assert vowels_count("why") == 1
assert vowels_count("sky") == 1
assert vowels_count("python") == 1
assert vowels_count("") == 0
assert vowels_count("BCDFG") == 0
