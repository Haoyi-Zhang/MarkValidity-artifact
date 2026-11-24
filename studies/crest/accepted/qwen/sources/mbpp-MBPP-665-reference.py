
def move_last(num_list):
    if not num_list:
        return num_list
    return num_list[1:] + num_list[:1]
