
def maximum_segments(n, a, b, c):
    dp = [0] * (n + 1)
    
    for i in range(1, n + 1):
        if i >= a:
            dp[i] = max(dp[i], dp[i - a] + 1)
        if i >= b:
            dp[i] = max(dp[i], dp[i - b] + 1)
        if i >= c:
            dp[i] = max(dp[i], dp[i - c] + 1)
    
    return dp[n]
