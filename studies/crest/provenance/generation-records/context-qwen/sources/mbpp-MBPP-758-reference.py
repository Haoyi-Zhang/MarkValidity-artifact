
def unique_sublists(list1):
    from collections import defaultdict
    count_dict = defaultdict(int)
    for sublist in list1:
        count_dict[tuple(sublist)] += 1
    return dict(count_dict)
