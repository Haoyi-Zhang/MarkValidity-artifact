
def differ_At_One_Bit_Pos(a, b):
	xor_result = a ^ b
	return xor_result & (xor_result - 1) == 0
