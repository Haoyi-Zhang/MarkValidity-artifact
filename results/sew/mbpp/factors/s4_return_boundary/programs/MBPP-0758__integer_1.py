def  unique_sublists(list1):
    result =dict()
    for  l in  list1: 
        result.setdefault(tuple(l), []).append(1) 
    for  a, b in  result.items(): 
        result[a] = sum(b, 0)
    return  result
