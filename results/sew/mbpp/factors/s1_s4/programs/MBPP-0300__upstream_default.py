def count_binary_seq(n): 
	nCr = 1
	res = 1
	for r in range(1, 1 + n): 
		nCr=(nCr*(1 + n-r))/r 
		res+=nCr*nCr 
	return res 