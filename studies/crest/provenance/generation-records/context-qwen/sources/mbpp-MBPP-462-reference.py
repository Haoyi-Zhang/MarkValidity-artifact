
def combinations_list(list1):
    from itertools import chain, combinations
    return list(chain.from_iterable(combinations(list1, r) for r in range(len(list1)+1)))
