
    index = 0
    found = False
    while index < len(dlist) and not found:
        if dlist[index] == item:
            found = True
        else:
            index += 1
    return (found, index)
