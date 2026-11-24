
def count_first_elements(test_tup):
    for idx, ele in enumerate(test_tup):
        if isinstance(ele, tuple):
            return idx
    return len(test_tup)
