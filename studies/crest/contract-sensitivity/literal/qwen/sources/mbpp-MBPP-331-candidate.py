
def count_unset_bits(n):
	count = 0
	while n:
		if not (n & 1):
			count += 1
		n >>= 1
	return count
