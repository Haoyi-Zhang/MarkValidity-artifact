
def encode(message):
	shift_vowel = lambda c: chr(((ord(c.lower()) - 97 + 2) % 26) + 97).upper() if c.isupper() else chr(((ord(c.lower()) - 97 + 2) % 26) + 97)
    
	encoded_message = ''
	vowels = 'aeiouAEIOU'
	for char in message:
		if char.isalpha():
			if char in vowels:
				encoded_message += shift_vowel(char)
			else:
				encoded_message += char.swapcase()
		else:
			encoded_message += char
	return encoded_message
