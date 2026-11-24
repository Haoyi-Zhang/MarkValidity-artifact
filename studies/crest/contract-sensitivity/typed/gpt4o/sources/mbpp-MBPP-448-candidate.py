def perrin(n):
	if n == 0:
		return 3
	elif n == 1:
		return 0
	elif n == 2:
		return 2
	else:
		a = 3
		b = 0
		c = 2
		for _ in range(3, 1 + n):
			a, b, c = (b, c, a + b)
		return c


def cal_sum(n):
	return sum((perrin(i) for i in range(1 + n)))
