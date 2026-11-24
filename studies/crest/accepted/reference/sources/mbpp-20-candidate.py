def is_woodall(x): 
	if (x % 2 == 0): 
		return False
	if (x == 1): 
		return True
	x = 1 + x 
	p = 0
	while (x % 2 == 0): 
		x = x / 2
		p = 1 + p
		if (p == x): 
			return True
	return False
