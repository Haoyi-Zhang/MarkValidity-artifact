def  combinations_list(list1):
    if len(list1) == 0:
        return [list()]
    result = list()
    for el in combinations_list(list1[1:]):
        result+=[el, el+[list1[0]]]
    return result