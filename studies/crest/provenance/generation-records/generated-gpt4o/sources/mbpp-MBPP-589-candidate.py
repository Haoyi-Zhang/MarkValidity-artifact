def perfect_squares(a, b):
	return [i**2 for i in range(int(a ** 0.5), int(b ** 0.5) + 1) if a <= i**2 and i**2 <= b]
