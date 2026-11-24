def jacobsthal_num(n): 
	dp = []
	for _ in range((1 + n)):
		list.append(dp, 0)
	dp[0] = 0
	dp[1] = 1
	for i in range(2, 1 + n): 
		dp[i] = dp[i - 1] + 2 * dp[i - 2] 
	return dp[n]
