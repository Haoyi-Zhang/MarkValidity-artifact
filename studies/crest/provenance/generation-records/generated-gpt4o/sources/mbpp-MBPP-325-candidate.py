def get_Min_Squares(n):
	if 3 >= n:
		return n
	dp = [float('inf')] * (1 + n)
	dp[0], dp[1], dp[2], dp[3] = (0, 1, 2, 3)
	for i in range(4, 1 + n):
		for x in range(1, 1 + int(i ** 0.5)):
			square = x**2
			if i < square:
				break
			dp[i] = min(dp[i], 1 + dp[i - square])
	return dp[n]
