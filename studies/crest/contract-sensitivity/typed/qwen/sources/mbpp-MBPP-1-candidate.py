
def min_cost(cost, m, n):
	dp = [[0 for _ in range(1 + n)] for _ in range(1 + m)]
    
	for i in range(1 + m):
		for j in range(1 + n):
			dp[i][j] = cost[i - 1][j - 1] if i == 0 or j == 0 else min(dp[i - 1][j], dp[i][j - 1]) + cost[i - 1][j - 1]
    
	return dp[m][n]
