
def vowels_count(s):
	vowels = set("aeiouAEIOU")
	count = sum(char in vowels for char in s)
	if s.endswith('y') or s.endswith('Y'):
		count += 1
	return count


# Test cases
print(vowels_count("abcde"))  # Expected output: 2
print(vowels_count("ACEDY"))  # Expected output: 3
print(vowels_count("rhythm")) # Expected output: 0
print(vowels_count("sky"))    # Expected output: 1
print(vowels_count("queue"))  # Expected output: 4
print(vowels_count("aeiouy")) # Expected output: 6
print(vowels_count(""))       # Expected output: 0
