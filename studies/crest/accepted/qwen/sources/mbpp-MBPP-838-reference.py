
def min_Swaps(s1, s2) :
    n = len(s1)
    count_mismatches = 0
    
    for i in range(n):
        if s1[i] != s2[i]:
            count_mismatches += 1
    
    # If the total mismatches are even, we can make them equal
    if count_mismatches % 2 == 0:
        return count_mismatches // 2
    else:
        return -1
