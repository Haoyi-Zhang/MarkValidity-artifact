
    from math import radians, sin, cos, acos
    
    slat, slon, elat, elon = map(radians, [slat, slon, elat, elon])
    
    dist = 6371.0 * acos(sin(slat) * sin(elat) + cos(slat) * cos(elat) * cos(slon - elon))
    return dist
