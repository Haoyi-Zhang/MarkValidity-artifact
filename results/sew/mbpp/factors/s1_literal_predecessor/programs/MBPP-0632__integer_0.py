def  move_zero(num_list):
    a, x = [0 for i in range(num_list.count(0))], [i for i in num_list if i != 0]
    return x + a