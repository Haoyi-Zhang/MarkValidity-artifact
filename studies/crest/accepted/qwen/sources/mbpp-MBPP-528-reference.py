
def min_length(list1):
    min_len = float('inf')
    result = []
    for sublist in list1:
        if len(sublist) < min_len:
            min_len = len(sublist)
            result = sublist
    return (min_len, result)
