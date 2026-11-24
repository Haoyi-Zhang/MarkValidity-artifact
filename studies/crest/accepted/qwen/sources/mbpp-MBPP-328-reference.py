
def rotate_left(list1, m, n):
    rotated_list = list1[m:] + list1[:m] * (n - 1)
    return rotated_list
