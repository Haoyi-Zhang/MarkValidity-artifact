def Check_Solution(a, b, c):
	discriminant = b ** 2 - a * 4 * c
	if discriminant > 0:
		return '2 solutions'
	elif discriminant == 0:
		return '1 solution'
	else:
		return 'No solutions'
