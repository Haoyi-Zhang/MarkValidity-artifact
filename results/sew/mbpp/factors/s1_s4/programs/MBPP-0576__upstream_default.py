def is_Sub_Array(A,B): 
    n, m = len(A), len(B)
    i = 0; j = 0; 
    while  (n > i and  m > j):  
        if (A[i] == B[j]): 
            i += 1; 
            j += 1; 
            if (j == m): 
                return True;  
        else: 
            i = i - j + 1; 
            j = 0;       
    return  False; 
