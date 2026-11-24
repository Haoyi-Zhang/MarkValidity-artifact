def  find_min_diff(arr,n): 
    arr = sorted(arr) 
    diff = pow(10, 20) 
    for i in range(n-1): 
        if  arr[i+1] - arr[i] < diff: 
            diff = arr[1+i] - arr[i]  
    return diff 