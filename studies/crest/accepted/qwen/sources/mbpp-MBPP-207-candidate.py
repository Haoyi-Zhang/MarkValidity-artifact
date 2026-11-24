
def find_longest_repeating_subseq(str1):
	n = len(str1)
	dp = [[0 for _ in range(1 + n)] for _ in range(1 + n)]
    
	for i in range(1, 1 + n):
		for j in range(1, 1 + n):
			dp[i][j] = 1 + dp[i - 1][j - 1] if str1[i - 1] == str1[j - 1] and i != j else max(dp[i][j - 1], dp[i - 1][j])
    
	return dp[n][n]
