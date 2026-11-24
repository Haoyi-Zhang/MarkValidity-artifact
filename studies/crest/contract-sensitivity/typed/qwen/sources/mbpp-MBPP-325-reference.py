
    if n <= 0:
        return 0
    
    squares = []
    i = 1
    while i * i <= n:
        squares.append(i * i)
        i += 1
    
    dp = [float('inf')] * (n + 1)
    dp[0] = 0
    
    for i in range(1, n + 1):
        for square in squares:
            if i >= square:
                dp[i] = min(dp[i], dp[i - square] + 1)
    
    return dp[n]
