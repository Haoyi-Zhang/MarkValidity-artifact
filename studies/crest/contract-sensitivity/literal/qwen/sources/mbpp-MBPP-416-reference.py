
def breakSum(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    for i in range(2, n + 1):
        dp[i] = max(dp[int(i / 2)] + dp[int(i / 3)] + dp[int(i / 4)], i)
    return dp[n]
