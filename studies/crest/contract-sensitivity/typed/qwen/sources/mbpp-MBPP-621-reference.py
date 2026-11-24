
def increment_numerics(test_list, K):
    return [str(int(x) + K) if x.isdigit() else x for x in test_list]
