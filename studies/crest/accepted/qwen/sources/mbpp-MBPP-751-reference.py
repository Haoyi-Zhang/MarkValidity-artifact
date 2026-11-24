
def check_min_heap(arr, i):
    n = len(arr)
    if 2 * i + 2 > n:
        return True
    if arr[i] > arr[2 * i + 1] or arr[i] > arr[2 * i + 2]:
        return False
    return check_min_heap(arr, 2 * i + 1) and check_min_heap(arr, 2 * i + 2)
