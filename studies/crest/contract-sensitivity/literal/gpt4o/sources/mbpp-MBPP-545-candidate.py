def toggle_F_and_L_bits(n):
	num_bits = n.bit_length()
	if 2 > num_bits:
		return n ^ 1
	mask = 1 << num_bits - 1 | 1
	return n ^ mask


print(toggle_F_and_L_bits(10))
print(toggle_F_and_L_bits(15))
print(toggle_F_and_L_bits(20))
