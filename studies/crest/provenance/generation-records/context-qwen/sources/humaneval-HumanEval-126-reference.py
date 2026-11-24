
def is_sorted(lst):
    for i in range(len(lst) - 1):
        if lst[i] > lst[i + 1]:
            return False
        if i > 0 and lst[i] == lst[i - 1] and lst[i] == lst[i + 1]:
            return False
    return True
