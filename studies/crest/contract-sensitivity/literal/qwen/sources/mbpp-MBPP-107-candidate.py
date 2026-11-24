
def count_Hexadecimal(L, R) :
	return sum(bool(hex(i).startswith('0x')) for i in range(L, R + 1))
