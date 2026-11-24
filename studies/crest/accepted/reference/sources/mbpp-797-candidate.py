def sum_odd(n): 
	terms = (1 + n) // 2
	return terms**2  


def sum_in_range(l, r): 
	return sum_odd(r) - sum_odd(l - 1)
