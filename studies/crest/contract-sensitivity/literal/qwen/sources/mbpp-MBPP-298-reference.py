
def intersection_nested_lists(l1, l2):
    return [[element for element in sublist if element in l1] for sublist in l2]
