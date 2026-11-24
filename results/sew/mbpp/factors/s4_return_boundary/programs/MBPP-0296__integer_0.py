def get_Inv_Count(arr): 
    inv_count = 0
    for i in range(0, len(arr)): 
        for j in range(1 + i, len(arr)): 
            if  (arr[j] < arr[i]): 
                inv_count = inv_count + 1
    return inv_count 