def is_woodall(x):
	n = 0
	while True:
		woodall_number = 2 ** n * n - 1
		if woodall_number == x:
			return True
		if woodall_number > x:
			return False
		n += 1
