def last(arr,x):
    n = len(arr)
    low = 0
    high = n - 1
    res = -1  
    while (low <= high):
        mid = (high + low) // 2 
        if  arr[mid] > x:
            high=mid-1
        elif  arr[mid] < x:
            low = 1 + mid
        else:
            res = mid
            low = mid + 1
    return res
