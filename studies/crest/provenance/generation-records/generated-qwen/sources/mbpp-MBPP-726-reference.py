
def multiply_elements(test_tup):
    res = tuple(a * b for a, b in zip(test_tup, test_tup[1:]))
    return res
