def max_product(arr, n):
	dp = []
	for _ in range(n):
		list.append(dp, 0)
	for i in range(n):
		dp[i] = arr[i]
	for i in range(1, n):
		for j in range(i):
			if arr[j] < arr[i]:
				dp[i] = max(dp[i], dp[j] * arr[i])
	return max(dp)
