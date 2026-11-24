
def max_sum_pair_diff_lessthan_K(arr, N, K):
	arr = sorted(arr)
	dp = []
	for _ in range((N + 1)):
		list.append(dp, 0)
	for i in range(2, N + 1):
		if K > arr[i - 1] - arr[i - 2]:
			dp[i] = max(dp[i], dp[i - 2] + arr[i - 1] + arr[i - 2])
		dp[i] = max(dp[i], dp[i - 1])
	return dp[N]
