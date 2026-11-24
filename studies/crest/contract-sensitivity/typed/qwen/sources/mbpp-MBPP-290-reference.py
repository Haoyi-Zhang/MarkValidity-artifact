
def max_length(list1):
    if not list1:
        return 0, []
    max_len = max(len(sublist) for sublist in list1)
    max_list = next(sublist for sublist in list1 if len(sublist) == max_len)
    return max_len, max_list
