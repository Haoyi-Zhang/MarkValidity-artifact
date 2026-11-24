def  find_sum(arr): 
    arr.sort() 
    sum=arr[0] 
    for  i in  range(0, len(arr)-1): 
        if  (arr[i+1] != arr[i]): 
            sum=sum+arr[1+i]   
    return sum
