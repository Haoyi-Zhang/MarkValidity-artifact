
def triangle_area(a, b, c):
	if a + b > c and a + c > b and b + c > a:
		s = (a + b + c) / 2
		area = ((s - a) * s * (s - b) * (s - c)) ** 0.5
		return round(area, 2)
	return -1
