
    if s <= 0:
        return 0
    x = y = z = s // 3
    if s % 3 != 0:
        z += s % 3
    return x * y * z
