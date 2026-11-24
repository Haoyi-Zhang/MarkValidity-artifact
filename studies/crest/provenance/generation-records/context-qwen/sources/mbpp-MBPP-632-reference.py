
def move_zero(num_list):
    non_zeroes = [num for num in num_list if num != 0]
    zeroes = [0] * (len(num_list) - len(non_zeroes))
    return non_zeroes + zeroes
