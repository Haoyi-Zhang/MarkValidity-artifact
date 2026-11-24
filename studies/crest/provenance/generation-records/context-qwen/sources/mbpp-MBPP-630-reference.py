
def get_coordinates(test_tup):
    res = [[x + dx, y + dy] for dx in range(-1, 2) for dy in range(-1, 2)]
    return res
