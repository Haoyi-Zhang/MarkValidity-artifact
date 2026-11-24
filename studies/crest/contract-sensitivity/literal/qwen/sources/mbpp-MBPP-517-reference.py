
def largest_pos(list1):
    max_num = None
    for num in list1:
        if num > 0:
            if max_num is None or num > max_num:
                max_num = num
    return max_num
