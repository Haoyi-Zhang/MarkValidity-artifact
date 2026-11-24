
def find_Min(arr, low, high):
    if high < low:
        return arr[0]
    
    if high == low:
        return arr[low]
    
    mid = int(low + (high - low) / 2)
    
    if mid > 0 and arr[mid] < arr[mid - 1]:
        return arr[mid]
    
    if arr[mid] >= arr[low]:
        return find_Min(arr, mid + 1, high)
    else:
        return find_Min(arr, low, mid - 1)
