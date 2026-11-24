
def remove_replica(test_tup):
    ele_count = {}
    res = []
    for ele in test_tup:
        if ele in ele_count:
            ele_count[ele] += 1
        else:
            ele_count[ele] = 1
    for ele in test_tup:
        if ele_count[ele] > 1:
            res.append('MSP')
        else:
            res.append(ele)
    return tuple(res)
