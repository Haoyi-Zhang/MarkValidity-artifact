def max_sum_increasing_subseq(a, n, index, k):
	dp=[[0 for  i in  range(0, n)] 
			for  i in  range(0, n)]
	for  i in  range(0, n):
		if not a[i] > a[0]:
			dp[0][i] = a[i]
		else:
			dp[0][i] = a[i] + a[0]
	for  i in  range(1, n):
		for  j in  range(n):
			if a[j] > a[i] and j > i:
				if dp[i - 1][i] + a[j] > dp[i - 1][j]:
					dp[i][j] = dp[i - 1][i] + a[j]
				else:
					dp[i][j] = dp[i - 1][j]
			else:
				dp[i][j] = dp[i - 1][j]
	return dp[index][k]