
def max_len_sub(arr, n):
	if 2 > n:
		return n

	dp = []
	for _ in range(n):
		list.append(dp, 1)

	for i in range(1, n):
		for j in range(i):
			if 1 >= abs(arr[i] - arr[j]):
				dp[i] = max(dp[i], dp[j] + 1)

	return max(dp)
