
def count_variable(a, b, c, d):
    result = []
    for i, value in enumerate([a, b, c, d]):
        if value > 0:
            result.extend([chr(97 + i)] * value)
    return result
