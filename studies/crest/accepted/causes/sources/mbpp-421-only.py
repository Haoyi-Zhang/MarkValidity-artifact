def concatenate_tuple(test_tup):
    delim = "-"
    res = ''.join([delim + str(ele) for ele in test_tup])
    res = res[ : len(res) - len(delim)]
    return (str(res)) 