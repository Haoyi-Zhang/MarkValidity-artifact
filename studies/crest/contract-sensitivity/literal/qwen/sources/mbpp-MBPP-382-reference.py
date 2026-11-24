
def find_rotation_count(A):
    low = 0
    high = len(A) - 1
    
    while low <= high:
        if A[low] <= A[high]:
            return low
        
        mid = (low + high) // 2
        next_index = (mid + 1) % len(A)
        prev_index = (mid - 1 + len(A)) % len(A)
        
        if A[mid] <= A[next_index] and A[mid] <= A[prev_index]:
            return mid
        
        if A[mid] <= A[high]:
            high = mid - 1
        else:
            low = mid + 1
    
    return 0
