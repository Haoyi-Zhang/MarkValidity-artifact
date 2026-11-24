def parabola_focus(a, b, c):
	h = -b / (2 * a)
	k = (a * 4 * c - b ** 2 + 1) / (a * 4)
	return (h, k)
