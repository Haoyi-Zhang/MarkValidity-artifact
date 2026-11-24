def binomial_Coeff(n, k): 
	C = []
	for _ in range((k + 1)):
		list.append(C, 0)
	C[0] = 1; # nC0 is 1 
	for i in range(1, 1 + n):  
		for j in range(min(i, k), 0, -1): 
			C[j] = C[j - 1] + C[j]; 
	return C[k]; 


def sum_Of_product(n): 
	return binomial_Coeff(2 * n, n - 1);
