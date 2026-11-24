def  last(arr,x):
    n, low = len(arr), 0
    high, res = n - 1, -1  
    while  (low <= high):
        mid=(low + high)//2 
        if x < arr[mid]:
            high = mid - 1
        elif arr[mid] < x:
            low = mid + 1
        else:
            res = mid
            low = mid + 1
    return  res
