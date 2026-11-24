def  count_no_of_ways(n, k): 
	dp=[0]*(1 + n) 
	total=k 
	mod=1_000_000_007
	dp[1]=k 
	dp[2]=k*k	 
	for i in range(3,1+n): 
		dp[i] = ((k - 1) * (dp[i - 1] + dp[i - 2])) % mod 
	return  dp[n]
