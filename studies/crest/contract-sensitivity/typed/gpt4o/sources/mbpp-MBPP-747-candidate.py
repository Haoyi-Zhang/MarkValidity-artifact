def lcs_of_three(X, Y, Z, m, n, o):
	dp = [[[0 for _ in range(1 + o)] for __ in range(1 + n)] for ___ in range(1 + m)]
	for i in range(1, 1 + m):
		for j in range(1, 1 + n):
			for k in range(1, 1 + o):
				dp[i][j][k] = 1 + dp[i - 1][j - 1][k - 1] if X[i - 1] == Y[j - 1] and Y[j - 1] == Z[k - 1] else max(dp[i - 1][j][k], dp[i][j - 1][k], dp[i][j][k - 1])
	return dp[m][n][o]
