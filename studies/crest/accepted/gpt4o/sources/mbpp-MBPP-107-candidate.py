def count_Hexadecimal(L, R):
	return sum((bool(any((char in 'ABCDEF' for char in hex(i)[2:].upper()))) for i in range(L, R + 1)))
