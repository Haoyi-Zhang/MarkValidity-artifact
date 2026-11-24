def any_int(x, y, z):
	if all(isinstance(i, int) for i in (x, y, z)):
		return x == y + z or y == z + x or z == y + x
	return False
