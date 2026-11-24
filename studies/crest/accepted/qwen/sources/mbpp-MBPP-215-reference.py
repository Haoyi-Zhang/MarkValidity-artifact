
def decode_list(alist):
    decoded = []
    for item in alist:
        if isinstance(item, list) and len(item) == 2:
            count, value = item
            decoded.extend([value] * count)
        else:
            decoded.append(item)
    return decoded
