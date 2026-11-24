def jacobsthal_num(n): 
	dp = []
	for _ in range((n + 1)):
		list.append(dp, 0)
	dp[0] = 0
	dp[1] = 1
	for i in range(2, n + 1): 
		dp[i] = dp[i - 1] + 2 * dp[i - 2] 
	return dp[n]
