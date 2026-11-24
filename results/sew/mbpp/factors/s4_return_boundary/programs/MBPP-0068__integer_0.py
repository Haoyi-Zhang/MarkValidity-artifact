def  is_Monotonic(A): 
    return (all(A[i] <= A[i + 1] for i in range(0, len(A) - 1)) or
            all(A[i] >= A[i + 1] for i in range(0, len(A) - 1))) 