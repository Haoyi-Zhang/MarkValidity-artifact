
def extract_min_max(test_tup, K):
    sorted_tup = sorted(test_tup)
    return tuple(sorted_tup[:K] + sorted_tup[-K:])
