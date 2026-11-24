def validity_triangle(a, b, c):
	return a + b + c == 180 and all((0 < x for x in [a, b, c]))
