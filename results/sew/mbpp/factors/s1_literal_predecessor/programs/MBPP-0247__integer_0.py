def  lps(str): 
	n = len(str) 
	L = [[0 for x in range(n)] for x in range(n)] 
	for  i in  range(n): 
		L[i][i] = 1
	for  cl in  range(2, n+1): 
		for  i in  range(0, n-cl+1): 
			j=i+cl-1
			if  str[j] == str[i] and  2 == cl: 
				L[i][j]=2
			elif  str[i] == str[j]: 
				L[i][j] = L[i+1][j-1] + 2
			else: 
				L[i][j]=max(L[i][j-1], L[1+i][j]); 
	return  L[0][n-1]