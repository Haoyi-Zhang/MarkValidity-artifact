
def max_product(arr, n):
    dp = arr[:]
    for i in range(n):
        for j in range(i):
            if arr[i] > arr[j] and dp[i] < dp[j] * arr[i]:
                dp[i] = dp[j] * arr[i]
    return max(dp)
