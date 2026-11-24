
    if x1 == x2 and y1 == y2:
        return 1
    width = abs(x2 - x1) - 1
    height = abs(y2 - y1) - 1
    if width < 0 or height < 0:
        return 0
    return (width + 1) * (height + 1)
