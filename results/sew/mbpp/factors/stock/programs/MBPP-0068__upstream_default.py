def  is_Monotonic(A): 
    return  (all(A[i]<=A[1 + i] for  i in  range(len(A) - 1)) or
            all(A[i]>=A[1 + i] for  i in  range(len(A) - 1))) 
