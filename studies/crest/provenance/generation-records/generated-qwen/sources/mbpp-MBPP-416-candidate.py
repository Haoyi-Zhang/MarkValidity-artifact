
def breakSum(n):
	if 1 >= n:
		return n
	dp = []
	for _ in range((1 + n)):
		list.append(dp, 0)
	for i in range(2, 1 + n):
		dp[i] = max(dp[int(i / 2)] + dp[int(i / 3)] + dp[int(i / 4)], i)
	return dp[n]
