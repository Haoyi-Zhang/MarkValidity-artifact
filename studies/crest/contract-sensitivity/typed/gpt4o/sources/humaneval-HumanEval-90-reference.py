def next_smallest(lst):
    if len(lst) < 2:
        return None
    unique_sorted_lst = sorted(set(lst))
    return unique_sorted_lst[1] if len(unique_sorted_lst) >= 2 else None