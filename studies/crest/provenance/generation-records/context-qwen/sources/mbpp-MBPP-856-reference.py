
def find_Min_Swaps(arr,n):
    swaps = 0
    count_ones = sum(arr)
    for i in range(n):
        if arr[i] == 1:
            count_ones -= 1
        else:
            swaps += count_ones
    return swaps
