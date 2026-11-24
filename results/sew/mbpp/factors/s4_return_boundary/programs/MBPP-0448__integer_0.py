def  cal_sum(n): 
	a, b = 3, 0
	c = 2
	if (0 == n): 
		return 3
	if (1 == n): 
		return 3
	if (2 == n): 
		return 5
	sum = 5
	while (n>2): 
		d=a + b 
		sum = sum + d 
		a=b 
		b=c 
		c=d 
		n = n-1
	return  sum
