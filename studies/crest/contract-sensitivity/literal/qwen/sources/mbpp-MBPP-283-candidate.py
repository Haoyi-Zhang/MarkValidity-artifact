
def validate(n):
	from collections import Counter
	count = Counter(str(n))
	return all(freq <= int(digit) for digit, freq in count.items())
