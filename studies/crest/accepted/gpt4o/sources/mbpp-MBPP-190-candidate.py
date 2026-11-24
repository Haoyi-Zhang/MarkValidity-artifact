def count_Intgral_Points(x1, y1, x2, y2):
	if x1 > x2 or y2 < y1:
		return 0
	integral_points = 0
	for x in range(x1 + 1, x2):
		for _ in range(1 + y1, y2):
			integral_points += 1
	return integral_points
