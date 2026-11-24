def fibfib(n: int):
	if n in [0, 1]:
		return 0
	if n == 2:
		return 1
	a = 0
	b = 0
	c = 1
	for _ in range(3, 1 + n):
		a, b, c = b, c, a + b + c
	return c
