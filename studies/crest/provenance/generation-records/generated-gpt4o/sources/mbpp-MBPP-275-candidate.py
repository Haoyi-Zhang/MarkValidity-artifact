def get_Position(a, n, m):
	pos = 0
	while a:
		pos = (pos + m - 1) % len(a)
		last_removed = a.pop(pos)
	return last_removed
