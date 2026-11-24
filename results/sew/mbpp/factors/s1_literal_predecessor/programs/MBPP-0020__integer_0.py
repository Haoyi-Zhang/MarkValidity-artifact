def  is_woodall(x): 
	if (0 == x % 2): 
		return False
	if (1 == x): 
		return True
	x = x + 1 
	p = 0
	while (0 == x % 2): 
		x=x/2
		p=p + 1
		if  (p == x): 
			return True
	return  False
