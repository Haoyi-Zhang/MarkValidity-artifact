
def surfacearea_cone(r, h):
    import math
    l = math.sqrt(r**2 + h**2)
    return math.pi * r * (r + l)
