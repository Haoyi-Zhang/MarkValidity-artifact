
def tuple_to_dict(test_tup):
    res = dict(zip(test_tup[::2], test_tup[1::2]))
    return res
