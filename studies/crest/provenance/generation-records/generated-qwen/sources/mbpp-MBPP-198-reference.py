
import math

def largest_triangle(a, b):
    return 4 * a * b / math.sqrt((a + b) ** 2 - a * b)
