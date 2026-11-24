
def encode_list(list1):
    if not list1:
        return []
    
    encoded = [[1, list1[0]]]
    for item in list1[1:]:
        if item == encoded[-1][1]:
            encoded[-1][0] += 1
        else:
            encoded.append([1, item])
    return encoded
