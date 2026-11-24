
def find_missing(ar, N):
    low, high = 0, N - 1
    while low < high:
        mid = (low + high) // 2
        if ar[mid] == mid + 1:
            low = mid + 1
        else:
            high = mid
    return low + 1
