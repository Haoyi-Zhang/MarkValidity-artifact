def cycpattern_check(a, b):
	b_rotations = [b[i:] + b[:i] for i in range(len(b))]
	return any(rotation in a for rotation in b_rotations)
