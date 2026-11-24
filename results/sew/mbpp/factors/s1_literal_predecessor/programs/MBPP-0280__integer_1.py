def  sequential_search(dlist, item):
    pos, found = 0, False
    while  pos < len(dlist) and  not  found:
        if dlist[pos] == item:
            found = True
        else:
            pos = pos + 1
    return (found, pos)