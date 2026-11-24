
def cummulative_sum(test_list):
    total = sum(sum(sublist) for sublist in test_list)
    return total
