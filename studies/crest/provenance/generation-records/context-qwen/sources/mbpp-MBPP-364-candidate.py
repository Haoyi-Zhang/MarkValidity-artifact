def min_flip_to_make_string_alternate(str1):
	def flip(char):
		return '1' if char == '0' else '0'

	def count_flips(start):
		expected_char = start
		flips = 0
		for char in str1:
			if char != expected_char:
				flips += 1
			expected_char = flip(expected_char)
		return flips

	return min(count_flips('0'), count_flips('1'))
