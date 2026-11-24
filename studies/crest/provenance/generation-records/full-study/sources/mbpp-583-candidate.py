def catalan_number(num):
	if 1 >= num:
		return 1   
	return sum((catalan_number(num - i - 1) * catalan_number(i) for i in range(num)))
