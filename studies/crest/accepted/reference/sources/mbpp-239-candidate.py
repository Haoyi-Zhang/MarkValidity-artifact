def get_total_number_of_sequences(m, n): 
	T = [[0 for _ in range(1 + n)] for i in range(1 + m)] 
	for i in range(1 + m): 
		for j in range(1 + n): 
			T[i][j] = 0 if i == 0 or j == 0 or i < j else (i if j == 1 else T[i - 1][j] + T[i // 2][j - 1])
	return T[m][n]
