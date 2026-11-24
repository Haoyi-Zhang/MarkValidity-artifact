
def sum_Pairs(arr, n):
    arr.sort()
    total_sum = 0
    for i in range(n):
        total_sum += (arr[i] * i) - (arr[i] * (n - i - 1))
    return total_sum
