
def count_range_in_list(li, min, max):
    return sum(1 for x in li if min <= x <= max)
