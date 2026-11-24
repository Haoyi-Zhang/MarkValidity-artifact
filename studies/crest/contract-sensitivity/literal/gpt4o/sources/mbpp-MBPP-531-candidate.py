def min_coins(coins, m, V):
	dp = [float('inf')] * (V + 1)
	dp[0] = 0
	for i in range(1, V + 1):
		for j in range(m):
			if i >= coins[j]:
				dp[i] = min(dp[i], 1 + dp[i - coins[j]])
	return dp[V] if dp[V] != float('inf') else -1
