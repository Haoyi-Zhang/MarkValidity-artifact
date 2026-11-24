
def is_undulating(n):
	if len(n) < 3:
		return False
	if any((n[i] == n[i - 1] for i in range(1, len(n)))):
		return False
	return True
