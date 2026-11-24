def lps(s):
	n = len(s)
	dp = [[0] * n for _ in range(n)]
	for i in range(n):
		dp[i][i] = 1
	for cl in range(2, 1 + n):
		for i in range(n - cl + 1):
			j = i + cl - 1
			dp[i][j] = dp[i + 1][j - 1] + 2 if s[i] == s[j] else max(dp[i + 1][j], dp[i][j - 1])
	return dp[0][n - 1]
