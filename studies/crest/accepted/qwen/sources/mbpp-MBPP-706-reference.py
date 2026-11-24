
def is_subset(arr1, m, arr2, n):
    set1 = set(arr1[:m])
    set2 = set(arr2[:n])
    return set2.issubset(set1)
