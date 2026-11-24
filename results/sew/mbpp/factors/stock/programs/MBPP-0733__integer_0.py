def  find_first_occurrence(A, x):
    (left, right)=(0, len(A)-1)
    result=-1
    while  left <= right:
        mid=(right + left)//2
        if A[mid] == x:
            result, right = mid, mid - 1
        elif x < A[mid]:
            right = mid - 1
        else:
            left = 1 + mid
    return  result
