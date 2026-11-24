import math


def sector_area(r, a):
	if a > 360:
		return None
	return (r**2 * math.pi) * (a / 360)
