def count_Pairs(arr,n): 
    cnt=0; 
    for i in range(n): 
        for j in range(i + 1,n): 
            if (arr[j] != arr[i]): 
                cnt = cnt + 1; 
    return  cnt; 