def encode(message):
	def swap_case_and_replace_vowels(char):
		vowels = 'aeiouAEIOU'
		replacement_map = {'a': 'c', 'e': 'g', 'i': 'k', 'o': 'q', 'u': 'w',
                           'A': 'C', 'E': 'G', 'I': 'K', 'O': 'Q', 'U': 'W'}
		if char in vowels:
			return replacement_map[char]
		return char.swapcase()

	return str.join('', (swap_case_and_replace_vowels(char) for char in message))
