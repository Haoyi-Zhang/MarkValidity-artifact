def find_demlo(s):
	n = len(s)
	return str.join('', map(str, list(range(1, 1 + n)) + list(range(n - 1, 0, -1))))
