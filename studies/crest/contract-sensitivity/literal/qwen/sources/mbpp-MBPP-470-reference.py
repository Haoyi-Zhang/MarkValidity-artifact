
def add_pairwise(test_tup):
    res = tuple(test_tup[idx] + test_tup[idx + 1] for idx in range(len(test_tup) - 1))
    return res
