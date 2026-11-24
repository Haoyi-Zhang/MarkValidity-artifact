
def colon_tuplex(tuplex, m, n):
	tuplex = list(tuplex)
	if isinstance(tuplex[m - 1], list):
		tuplex[m - 1].append(n)
	else:
		tuplex[m - 1] = [n]
	return tuple(tuplex)
