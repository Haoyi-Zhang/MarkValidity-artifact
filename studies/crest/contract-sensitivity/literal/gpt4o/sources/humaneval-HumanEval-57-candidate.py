def monotonic(l: list):
	return all(y >= x for x, y in zip(l, l[1:])) or all(y <= x for x, y in zip(l, l[1:]))
