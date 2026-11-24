
import functools

def find_k_product(test_list, K):
    return functools.reduce(lambda x, y: x * y[K], test_list, 1)
