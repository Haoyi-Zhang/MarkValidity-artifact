def check_Triangle(x1, y1, x2, y2, x3, y3):
	if x1 == x2 and x2 == x3 or y1 == y2 and y2 == y3 or (y2 - y1) * (x3 - x2) == (x2 - x1) * (y3 - y2):
		return 'No'
	return 'Yes'
