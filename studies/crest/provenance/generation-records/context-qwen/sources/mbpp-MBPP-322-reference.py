
def position_min(list1):
    min_value = min(list1)
    positions = [index for index, value in enumerate(list1) if value == min_value]
    return positions
