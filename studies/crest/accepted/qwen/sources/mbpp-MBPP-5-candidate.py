
def count_ways(n):
	if n == 0:
		return 1
	elif n == 1:
		return 0
	else:
		a = 1
		b = 1
		for _ in range(2, 1 + n):
			a, b = b, (a + 4 * b) % 1000000007
		return b
