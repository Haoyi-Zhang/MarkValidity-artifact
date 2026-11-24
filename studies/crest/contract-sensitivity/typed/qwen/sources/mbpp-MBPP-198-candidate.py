
import math


def largest_triangle(a, b):
	return a * 4 * b / math.sqrt((a + b) ** 2 - a * b)
