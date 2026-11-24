
def maximum_segments(n, a, b, c):
	dp = []
	for _ in range((1 + n)):
		list.append(dp, 0)
    
	for i in range(1, 1 + n):
		if i >= a:
			dp[i] = max(dp[i], 1 + dp[i - a])
		if i >= b:
			dp[i] = max(dp[i], dp[i - b] + 1)
		if i >= c:
			dp[i] = max(dp[i], dp[i - c] + 1)
    
	return dp[n]
