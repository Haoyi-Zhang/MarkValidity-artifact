def min_of_three(a, b, c): 
	return a if (a <= b) and (a <= c) else (b if (a >= b) and (b <= c) else c)
