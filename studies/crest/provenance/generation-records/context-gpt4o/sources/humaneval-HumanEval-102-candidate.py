def choose_num(x, y):
	if y < x:
		return -1
	return next((num for num in range(y, x - 1, -1) if num % 2 == 0), -1)
