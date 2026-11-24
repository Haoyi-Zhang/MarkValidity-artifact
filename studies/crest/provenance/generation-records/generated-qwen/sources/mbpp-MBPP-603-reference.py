
def get_ludic(n):
    ludics = [i for i in range(1, n + 1)]
    index = 1
    while index < len(ludics):
        first_ludic = ludics[index]
        ludics = [x for i, x in enumerate(ludics) if (i + 1) % first_ludic != 0 or (i + 1) == first_ludic]
        index += 1
    return ludics
