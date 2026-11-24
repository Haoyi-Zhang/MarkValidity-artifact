def is_Sub_Array(A,B): 
    n = len(A)
    m = len(B)
    i = 0; j = 0; 
    while (n > i and m > j):  
        if not (A[i] == B[j]): 
            i = i - j + 1; 
            j = 0;  
        else: 
            i += 1; 
            j += 1; 
            if (j == m): 
                return True;       
    return False; 