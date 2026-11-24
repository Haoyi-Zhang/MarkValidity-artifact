
def matrix_to_list(test_list):
    return str([tuple(item[i] for item in sublist) for i in range(len(test_list[0][0]))])
