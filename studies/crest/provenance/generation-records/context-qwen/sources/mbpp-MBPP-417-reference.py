
def group_tuples(Input):
    result = {}
    for key, value in Input:
        if key in result:
            result[key].append(value)
        else:
            result[key] = [key, value]
    return list(tuple(v) for v in result.values())
