
import math


def sd_calc(data):
	n = len(data)
	mean = sum(data) / n
	variance = sum((x - mean) ** 2 for x in data) / n
	return math.sqrt(variance)
