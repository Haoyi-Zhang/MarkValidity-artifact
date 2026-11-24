
def check_greater(test_tup1, test_tup2):
    return all(b > a for a, b in zip(test_tup1, test_tup2))
