
def modular_sum(arr, n, m):
	dp = []
	for _ in range(m):
		list.append(dp, False)
	dp[0] = True
    
	for i in range(n):
		temp = []
		list.extend(temp, ((j + arr[i]) % m for j in range(m) if dp[j]))
		for k in temp:
			dp[k] = True
    
	return dp[0]
