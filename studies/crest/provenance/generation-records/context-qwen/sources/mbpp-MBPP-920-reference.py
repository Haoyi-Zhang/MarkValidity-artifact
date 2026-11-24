
def remove_tuple(test_list):
    return [tup for tup in test_list if not all(x is None for x in tup)]
