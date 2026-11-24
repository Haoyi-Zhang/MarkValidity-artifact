import math
def lateralsurface_cone(r,h):
  l=math.sqrt(r * r+h * h)
  LSA=r * math.pi  * l
  return LSA