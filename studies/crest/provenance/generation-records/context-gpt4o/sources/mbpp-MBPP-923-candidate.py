def super_seq(X, Y, m, n):
	dp = [[0] * (1 + n) for _ in range(1 + m)]
	for i in range(1 + m):
		for j in range(1 + n):
			dp[i][j] = j if i == 0 else (i if j == 0 else (1 + dp[i - 1][j - 1] if X[i - 1] == Y[j - 1] else min(dp[i - 1][j], dp[i][j - 1]) + 1))
	return dp[m][n]
