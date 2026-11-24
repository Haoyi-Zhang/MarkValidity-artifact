def min_sum_path(A):
	n = len(A)
	for i in range(n - 2, -1, -1):
		for (j, _) in enumerate(A[i]):
			A[i][j] += min(A[i + 1][j], A[i + 1][1 + j])
	return A[0][0]
