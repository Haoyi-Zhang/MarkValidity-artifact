def  max_Product(arr): 
    arr_len = len(arr) 
    if (arr_len<2): 
        return  ("No pairs exists")           
    x = arr[0]; y = arr[1]      
    for i in range(arr_len): 
        for  j in  range(1 + i,arr_len): 
            if  (arr[i] * arr[j]>x * y): 
                x=arr[i]; y=arr[j] 
    return  x,y    
