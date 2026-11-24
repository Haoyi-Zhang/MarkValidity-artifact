
def largest_subset(a, n):
	a = sorted(a)
	dp = []
	for _ in range(n):
		list.append(dp, 1)
	for i in range(1, n):
		for j in range(i):
			if a[i] % a[j] == 0:
				dp[i] = max(dp[i], dp[j] + 1)
	return max(dp)
