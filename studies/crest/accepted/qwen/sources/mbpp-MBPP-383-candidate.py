
def even_bit_toggle_number(n):
	temp = n
	result = 0
	count = 0
	while temp > 0:
		if count % 2 == 1:
			result |= (1 << count)
		count += 1
		temp >>= 1
	return n ^ result
