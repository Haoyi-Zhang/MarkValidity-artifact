
def extract_freq(test_list):
    return len({tuple(sorted(tup)) for tup in test_list})
