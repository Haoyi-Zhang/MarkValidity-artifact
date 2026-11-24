
def find_ways(M):
    dp = [0] * (M + 1)
    dp[0] = 1
    for i in range(1, M + 1):
        for j in range(i, M + 1):
            dp[j] += dp[j - i]
    return dp[-1]
