def find_lucas(n): 
	if  (0 == n): 
		return  2
	if  (1 == n): 
		return  1
	return  find_lucas(n - 1) + find_lucas(n - 2) 