from math import tan, pi
def  area_polygon(s, l):
  area = s * (l ** 2) / (tan(pi / s) * 4)
  return  area