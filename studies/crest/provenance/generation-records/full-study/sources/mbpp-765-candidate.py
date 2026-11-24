import math 


def is_polite(n): 
	n = 1 + n
	return (int)(n + (math.log((math.log(n, 2) + n), 2)))
