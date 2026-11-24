
def max_profit(price, k):
	if not price:
		return 0

	n = len(price)
	dp = [[0] * (k + 1) for _ in range(n)]

	for j in range(1, k + 1):
		max_diff = -price[0]
		for i in range(1, n):
			dp[i][j] = max(dp[i - 1][j], max_diff + price[i])
			max_diff = max(max_diff, dp[i - 1][j - 1] - price[i])

	return dp[n - 1][k]
