def count_no_of_ways(n, k): 
	dp = []
	for _ in range((n + 1)):
		list.append(dp, 0)
	total = k 
	dp[1] = k 
	dp[2] = k**2	 
	mod = 1000000007
	for i in range(3, n + 1): 
		dp[i] = ((k - 1) * (dp[i - 1] + dp[i - 2])) % mod 
	return dp[n]
