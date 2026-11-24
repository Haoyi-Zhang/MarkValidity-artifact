
def iscube(a):
    if a >= 0:
        n = round(a ** (1/3))
        return n ** 3 == a
    else:
        n = round(-((-a) ** (1/3)))
        return n ** 3 == a
