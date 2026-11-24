
def max_sum(arr, n):
    inc = [0 for i in range(n)]
    dec = [0 for i in range(n)]

    # Length of increasing subsequence ending at all indexes
    for i in range(0, n):
        inc[i] = 1
        for j in range(0, i):
            if arr[i] > arr[j] and inc[i] < inc[j] + 1:
                inc[i] = inc[j] + 1

    # Length of decreasing subsequence starting at all indexes
    for i in range(n-1, -1, -1):
        dec[i] = 1
        for j in range(n-1, i, -1):
            if arr[i] > arr[j] and dec[i] < dec[j] + 1:
                dec[i] = dec[j] + 1

    # Find the maximum value of inc[i] + dec[i] - 1
    max_sum = -1
    for i in range(0, n):
        if (inc[i] + dec[i] - 1) > max_sum:
            max_sum = (inc[i] + dec[i] - 1)

    return max_sum
