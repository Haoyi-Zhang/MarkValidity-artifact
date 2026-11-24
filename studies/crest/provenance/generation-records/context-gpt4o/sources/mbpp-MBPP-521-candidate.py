def check_isosceles(x, y, z):
	if y + x > z and z + x > y and (y + z > x):
		return len(set([x, y, z])) == 2
	return False
