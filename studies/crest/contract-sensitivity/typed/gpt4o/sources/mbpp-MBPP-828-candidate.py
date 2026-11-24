def count_alpha_dig_spl(string):
	alphabets = 0
	digits = 0
	special_chars = 0
	for char in string:
		if char.isalpha():
			alphabets += 1
		elif char.isdigit():
			digits += 1
		else:
			special_chars += 1
	return (alphabets, digits, special_chars)
