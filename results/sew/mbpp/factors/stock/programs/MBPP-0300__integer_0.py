def  count_binary_seq(n): 
	nCr = res = 1
	for r in range(1, n + 1): 
		nCr=(nCr*(1 + n-r))/r 
		res = res + nCr * nCr 
	return  res 