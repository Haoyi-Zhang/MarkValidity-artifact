def is_sorted(lst):
    if len(lst) <= 1:
        return True
    for i in range(1, len(lst)):
        if lst[i] < lst[i - 1]:
            return False
    counts = {}
    for num in lst:
        if num in counts:
            counts[num] += 1
            if counts[num] > 2:
                return False
        else:
            counts[num] = 1
    return True