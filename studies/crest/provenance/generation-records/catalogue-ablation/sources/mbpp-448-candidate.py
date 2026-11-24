def cal_sum(n): 
	if (n == 0): 
		return 3
	if (n == 1): 
		return 3
	if (n == 2): 
		return 5
	sum = 5
	a = 3
	b = 0
	c = 2
	while (2 < n): 
		d = a + b 
		sum = sum + d 
		a = b 
		b = c 
		c = d 
		n = n - 1
	return sum
