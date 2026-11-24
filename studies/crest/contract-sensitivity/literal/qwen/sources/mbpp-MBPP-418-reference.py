
def Find_Max(lst):
    if not lst:
        return []
    max_list = max(lst, key=len)
    return max_list
