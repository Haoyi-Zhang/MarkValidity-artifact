
def get_noOfways(n):
	if 0 >= n:
		return 0
	elif n in [1, 2]:
		return 1
	else:
		a = 1
		b = 1
		for _ in range(3, 1 + n):
			a, b = b, a + b
		return b
