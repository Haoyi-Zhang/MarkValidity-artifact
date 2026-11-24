
def lcm(x, y):
	greater = x if y < x else y

	while (True):
		if ((greater % x == 0) and (greater % y == 0)):
			lcm = greater
			break
		greater += 1

	return lcm
