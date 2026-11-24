def get_coordinates(test_tup):
	x, y = test_tup
	return [[i, j] for i in range(x - 1, 2 + x) for j in range(y - 1, 2 + y)]
