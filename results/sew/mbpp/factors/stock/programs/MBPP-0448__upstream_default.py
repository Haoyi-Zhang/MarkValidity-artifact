def  cal_sum(n): 
	a = 3
	b = 0
	c=2
	if  (n == 0): 
		return 3
	if  (n == 1): 
		return 3
	if  (n == 2): 
		return 5
	sum=5
	while (n>2): 
		d = b + a 
		sum += d 
		a = b 
		b = c 
		c = d 
		n -= 1
	return  sum
