
def count_Rectangles(radius):
	if radius < 1:
		return 0
	n = int(radius // 1)
	return 2 * (n * (1 + n))
