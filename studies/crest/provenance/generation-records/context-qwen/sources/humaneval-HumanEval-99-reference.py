
def closest_integer(value):
    float_value = float(value)
    if float_value > 0:
        return int(float_value + 0.5)
    else:
        return int(float_value - 0.5)
