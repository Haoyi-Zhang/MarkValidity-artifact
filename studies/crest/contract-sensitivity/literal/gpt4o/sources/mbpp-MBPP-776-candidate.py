def count_vowels(test_str):
	vowels = 'aeiouAEIOU'
	return sum((bool(test_str[i] not in vowels and (test_str[i - 1] in vowels or test_str[i + 1] in vowels)) for i in range(1, len(test_str) - 1)))
