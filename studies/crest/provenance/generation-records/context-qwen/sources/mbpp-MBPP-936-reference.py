
def re_arrange_tuples(test_list, ord_list):
    return sorted(test_list, key=lambda x: ord_list.index(x[0]))
