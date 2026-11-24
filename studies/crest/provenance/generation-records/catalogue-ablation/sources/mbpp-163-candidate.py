from math import tan, pi


def area_polygon(s, l):
	return (l ** 2) * s / (tan(pi / s) * 4)
