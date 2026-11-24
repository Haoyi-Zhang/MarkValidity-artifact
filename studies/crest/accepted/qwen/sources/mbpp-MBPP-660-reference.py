
def find_Points(l1, r1, l2, r2):
    if r1 < l2:
        return (r1, l2)
    elif r2 < l1:
        return (l2, r1)
    else:
        return (min(l1, l2), max(r1, r2))
