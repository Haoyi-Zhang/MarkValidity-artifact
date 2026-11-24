def get_total_number_of_sequences(m,n): 
	T = [[0 for  i in  range(n+1)] for  i in  range(m+1)] 
	for  i in  range(m+1): 
		for  j in  range(0, n+1): 
			if 0==i or 0==j: 
				T[i][j] = 0
			elif i<j: 
				T[i][j]=0
			elif 1==j: 
				T[i][j]=i 
			else: 
				T[i][j]=T[i-1][j]+T[i//2][j-1] 
	return  T[m][n]