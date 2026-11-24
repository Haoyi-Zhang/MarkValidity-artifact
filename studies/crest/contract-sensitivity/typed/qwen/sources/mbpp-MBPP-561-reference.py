
def assign_elements(test_list):
    result = {}
    for a, b in test_list:
        if a not in result:
            result[a] = []
        if b not in result:
            result[b] = []
        if a in [x[1] for x in test_list]:
            result[b].append(a)
        if b in [x[0] for x in test_list]:
            result[a].append(b)
    return result
