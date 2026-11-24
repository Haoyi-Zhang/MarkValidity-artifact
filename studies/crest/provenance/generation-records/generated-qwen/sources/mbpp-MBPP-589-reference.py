
import math

def perfect_squares(a, b):
    start = math.ceil(math.sqrt(a))
    end = math.floor(math.sqrt(b))
    return [i**2 for i in range(start, end + 1)]
