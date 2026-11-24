
def longest_subseq_with_diff_one(arr, n):
	from collections import defaultdict

	dp = []
	for _ in range(n):
		list.append(dp, 0)

	for i in range(n):
		dp[i] = 1
		if arr[i] - 1 in dp:
			dp[i] = max(dp[i], dp[arr.index(arr[i] - 1)] + 1)
		if 1 + arr[i] in dp:
			dp[i] = max(dp[i], dp[arr.index(1 + arr[i])] + 1)
	max_length = 0

	for length in dp:
		max_length = max(max_length, length)

	return max_length
