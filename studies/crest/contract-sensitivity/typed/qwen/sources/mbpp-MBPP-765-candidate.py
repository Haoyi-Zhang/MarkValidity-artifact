
def is_polite(n):
	return n + int((n + math.log2(0.5 + n)).bit_length())
