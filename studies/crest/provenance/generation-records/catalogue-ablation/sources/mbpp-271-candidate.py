def even_Power_Sum(n): 
	sum = 0; 
	for i in range(1, n + 1): 
		j = i * 2; 
		sum = sum + (j**2 * j * j * j); 
	return sum;
