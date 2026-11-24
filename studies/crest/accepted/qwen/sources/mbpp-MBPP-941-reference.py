
def count_elim(num):
    for i, element in enumerate(num):
        if isinstance(element, tuple):
            return i
    return len(num)
