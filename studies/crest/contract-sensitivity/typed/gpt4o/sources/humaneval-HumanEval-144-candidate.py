def simplify(x, n):
	x_num, x_den = map(int, x.split('/'))
	n_num, n_den = map(int, n.split('/'))
    
	result_num = n_num * x_num
	result_den = n_den * x_den
    
	return result_num % result_den == 0
