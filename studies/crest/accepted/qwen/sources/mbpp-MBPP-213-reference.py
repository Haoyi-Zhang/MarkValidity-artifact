
def concatenate_strings(test_tup1, test_tup2):
    res = tuple(a + b for a, b in zip(test_tup1, test_tup2))
    return res
