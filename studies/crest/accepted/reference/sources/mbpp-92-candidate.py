def is_undulating(n): 
	n = str(n)
	if (2 >= len(n)): 
		return False
	if any(((n[i - 2] != n[i]) for i in range(2, len(n)))):
		return False
	return True
