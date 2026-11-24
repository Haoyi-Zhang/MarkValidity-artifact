def  last(arr,x):
    n, low = len(arr), 0
    high, res = n - 1, -1  
    while  (low <= high):
        mid=(high + low)//2 
        if x < arr[mid]:
            high = mid - 1
        elif arr[mid] < x:
            low=mid + 1
        else:
            res, low = mid, mid + 1
    return res