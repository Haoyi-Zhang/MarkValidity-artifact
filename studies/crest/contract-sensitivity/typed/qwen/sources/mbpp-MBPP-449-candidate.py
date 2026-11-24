
def check_Triangle(x1, y1, x2, y2, x3, y3):
	a = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
	b = ((x3 - x2)**2 + (y3 - y2)**2)**0.5
	c = ((y3 - y1)**2 + (x3 - x1)**2)**0.5
	if a + b > c and a + c > b and b + c > a:
		return 'Yes'
	return 'No'
