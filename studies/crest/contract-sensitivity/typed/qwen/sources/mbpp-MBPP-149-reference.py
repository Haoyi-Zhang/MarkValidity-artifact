
def longest_subseq_with_diff_one(arr, n):
    from collections import defaultdict

    dp = [0] * n
    max_length = 0

    for i in range(n):
        dp[i] = 1
        if arr[i] - 1 in dp:
            dp[i] = max(dp[i], dp[arr.index(arr[i] - 1)] + 1)
        if arr[i] + 1 in dp:
            dp[i] = max(dp[i], dp[arr.index(arr[i] + 1)] + 1)

    for length in dp:
        max_length = max(max_length, length)

    return max_length
