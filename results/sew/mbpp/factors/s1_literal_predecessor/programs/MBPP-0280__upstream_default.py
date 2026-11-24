def sequential_search(dlist, item):
    pos = 0
    found = False
    while pos<len(dlist) and not found:
        if not dlist[pos] == item:
            pos = pos + 1
        else:
            found = True
    return found, pos
