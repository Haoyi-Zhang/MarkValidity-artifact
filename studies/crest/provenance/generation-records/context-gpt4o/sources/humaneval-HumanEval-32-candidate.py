def find_zero(xs: list):
	if len(xs) % 2 != 0 or xs[-1] == 0:
		raise ValueError("Invalid list of coefficients")
	f = lambda x: poly(xs, x)
	a = -1e5
	b = 1e5
	while 1e-6 < b - a:
		c = (a + b) / 2
		if f(c) == 0:
			return c
		elif f(c) * f(a) < 0:
			b = c
		else:
			a = c
	return (a + b) / 2
