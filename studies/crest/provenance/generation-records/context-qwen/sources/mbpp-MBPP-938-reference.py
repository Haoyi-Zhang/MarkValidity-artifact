
def find_closet(A, B, C, p, q, r):
    i = 0
    j = 0
    k = 0
    
    diff = float('inf')
    min_i = 0
    min_j = 0
    min_k = 0
    
    while i < p and j < q and k < r:
        max_of_three = max(A[i], B[j], C[k])
        min_of_three = min(A[i], B[j], C[k])
        
        if abs(max_of_three - min_of_three) < diff:
            diff = max_of_three - min_of_three
            min_i = A[i]
            min_j = B[j]
            min_k = C[k]
        
        if diff == 0:
            break
        
        if A[i] == min_of_three:
            i += 1
        elif B[j] == min_of_three:
            j += 1
        else:
            k += 1
    
    return (min_i, min_j, min_k)
