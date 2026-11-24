
    total_sum = sum(arr)
    left_sum = 0
    for i in range(len(arr)):
        if left_sum == (total_sum - arr[i] - left_sum):
            return i
        left_sum += arr[i]
    return -1
