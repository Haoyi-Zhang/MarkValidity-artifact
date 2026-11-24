def max_Product(arr): 
    arr_len = len(arr) 
    if  (arr_len < 2): 
        return ("No pairs exists")           
    x = arr[0]; y = arr[1]      
    for  i in  range(0,arr_len): 
        for  j in  range(1 + i,arr_len): 
            if (arr[j] * arr[i] > y * x): 
                x=arr[i]; y=arr[j] 
    return x,y    