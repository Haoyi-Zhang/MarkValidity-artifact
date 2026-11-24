
def tuple_intersection(test_list1, test_list2):
    set1 = {frozenset(t) for t in test_list1}
    set2 = {frozenset(t) for t in test_list2}
    return {tuple(s) for s in set1 & set2}
