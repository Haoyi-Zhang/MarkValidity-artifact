def odd_num_sum(n) : 
	j = 0
	sm = 0
	for i in range(1, n + 1) : 
		j = (i * 2 - 1) 
		sm = sm + (j**2 * j * j)   
	return sm
