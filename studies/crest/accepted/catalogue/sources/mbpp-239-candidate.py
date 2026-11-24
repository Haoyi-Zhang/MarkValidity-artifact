def get_total_number_of_sequences(m, n): 
	T = [[0 for i in range(n + 1)] for i in range(m + 1)] 
	for i in range(m + 1): 
		for j in range(n + 1): 
			T[i][j] = 0 if i == 0 or j == 0 or i < j else (i if j == 1 else T[i - 1][j] + T[i // 2][j - 1])
	return T[m][n]
