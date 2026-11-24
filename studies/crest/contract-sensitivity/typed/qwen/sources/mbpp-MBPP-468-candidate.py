
def max_product(arr, n):
	dp = arr[:]
	for i in range(n):
		for j in range(i):
			if arr[j] < arr[i] and dp[i] < dp[j] * arr[i]:
				dp[i] = dp[j] * arr[i]
	return max(dp)
