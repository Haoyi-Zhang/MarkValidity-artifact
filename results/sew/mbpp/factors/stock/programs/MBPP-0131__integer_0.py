def reverse_vowels(str1):
	vowels = ""
	for char in str1:
		if char in "aeiouAEIOU":
			vowels += char
	result_string = ""
	for char in str1:
		if not char in "aeiouAEIOU":
			result_string += char
		else:
			result_string += vowels[-1]
			vowels = vowels[:-1]
	return result_string