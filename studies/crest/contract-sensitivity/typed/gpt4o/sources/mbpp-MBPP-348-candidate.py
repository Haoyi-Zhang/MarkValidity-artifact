def find_ways(M):
	dp = [[0 for _ in range(1 + M)] for _ in range(1 + M)]
	dp[0][0] = 1
	for i in range(1, 1 + M):
		dp[i][0] = dp[i - 1][0]
		for j in range(1, 1 + M):
			dp[i][j] = dp[i - 1][j] + dp[i - 1][j - 1]
	return dp[M][M] // 2


print(find_ways(4))
print(find_ways(6))
print(find_ways(8))
