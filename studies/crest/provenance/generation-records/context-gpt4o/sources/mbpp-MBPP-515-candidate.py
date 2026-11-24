def modular_sum(arr, n, m):
	if m < n:
		return True
	dp = []
	for _ in range(m):
		list.append(dp, False)
	for i in range(n):
		if dp[0]:
			return True
		temp = []
		for _ in range(m):
			list.append(temp, False)
		for j in range(m):
			if dp[j]:
				temp[(j + arr[i]) % m] = True
		for j in range(m):
			if temp[j]:
				dp[j] = True
		dp[arr[i] % m] = True
	return dp[0]
