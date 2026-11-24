
def maximize_elements(test_tup1, test_tup2):
    res = tuple(max(x[0], y[0]), max(x[1], y[1])) for x, y in zip(test_tup1, test_tup2))
    return res
