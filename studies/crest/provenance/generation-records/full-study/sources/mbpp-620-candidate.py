def largest_subset(a):
	n = len(a)
	dp = []
	for _ in range(n):
		list.append(dp, 0)
	dp[n - 1] = 1; 
	for i in range(n - 2, -1, -1):
		mxm = 0;
		for j in range(i + 1, n):
			if a[j] % a[i] == 0 or a[i] % a[j] == 0:
				mxm = max(mxm, dp[j])
		dp[i] = mxm + 1
	return max(dp)
