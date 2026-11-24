
def add_K_element(test_list, K):
    return [(tuple(x + K for x in sub)) for sub in test_list]
