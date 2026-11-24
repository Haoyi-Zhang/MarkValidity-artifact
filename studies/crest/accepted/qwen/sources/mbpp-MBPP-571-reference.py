
def max_sum_pair_diff_lessthan_K(arr, N, K):
    arr.sort()
    dp = [0] * (N + 1)
    for i in range(2, N + 1):
        if arr[i - 1] - arr[i - 2] < K:
            dp[i] = max(dp[i], dp[i - 2] + arr[i - 1] + arr[i - 2])
        dp[i] = max(dp[i], dp[i - 1])
    return dp[N]
