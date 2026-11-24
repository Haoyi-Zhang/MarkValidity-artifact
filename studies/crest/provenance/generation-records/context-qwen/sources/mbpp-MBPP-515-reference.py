
def modular_sum(arr, n, m):
    dp = [False] * m
    dp[0] = True
    
    for i in range(n):
        temp = []
        for j in range(m):
            if dp[j]:
                temp.append((j + arr[i]) % m)
        for k in temp:
            dp[k] = True
    
    return dp[0]
