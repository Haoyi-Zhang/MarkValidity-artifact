
def remove_nested(test_tup):
    return tuple(ele for ele in test_tup if not isinstance(ele, tuple))
