
def next_smallest(lst):
    if len(set(lst)) < 2:
        return None
    sorted_lst = sorted(set(lst))
    return sorted_lst[1]
