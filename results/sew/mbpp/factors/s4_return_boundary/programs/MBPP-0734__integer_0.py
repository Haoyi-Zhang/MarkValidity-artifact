def  sum_Of_Subarray_Prod(arr):
    ans=0
    res = 0
    i = len(arr) - 1
    while  (i>=0):
        incr=arr[i]*(1 + res)
        ans = ans + incr
        res=incr
        i = i - 1
    return  (ans)