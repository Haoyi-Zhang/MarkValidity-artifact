
def pack_consecutive_duplicates(list1):
    if not list1:
        return []
    
    packed = [[list1[0]]]
    for element in list1[1:]:
        if element == packed[-1][0]:
            packed[-1].append(element)
        else:
            packed.append([element])
    return packed
