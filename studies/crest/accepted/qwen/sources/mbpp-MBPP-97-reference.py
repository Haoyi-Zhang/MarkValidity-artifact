
def frequency_lists(list1):
    from collections import Counter
    flat_list = [item for sublist in list1 for item in sublist]
    return dict(Counter(flat_list))
