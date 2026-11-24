
def find_ways(M):
	dp = []
	for _ in range((1 + M)):
		list.append(dp, 0)
	dp[0] = 1
	for i in range(1, 1 + M):
		for j in range(i, 1 + M):
			dp[j] += dp[j - i]
	return dp[-1]
