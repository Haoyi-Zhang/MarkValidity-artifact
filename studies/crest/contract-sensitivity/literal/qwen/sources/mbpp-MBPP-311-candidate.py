
def set_left_most_unset_bit(n):
	if n == 0:
		return 1
	m = 1
	while m < 1 + n and (n & m) != 0:
		m <<= 1
	return n | m
