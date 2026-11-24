
def count_no_of_ways(n, k):
    if n == 0:
        return 0
    if n == 1:
        return k
    
    same = 0
    diff = k
    
    for i in range(2, n + 1):
        new_same = diff
        new_diff = (same + diff) * (k - 1)
        
        same = new_same
        diff = new_diff
    
    return same + diff
