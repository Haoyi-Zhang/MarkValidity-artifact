
    import math
    
    def area_polygon(s,l):
        return (s * l**2) / (4 * math.tan(math.pi / s))
    
    print(area_polygon(4,20))
    print(area_polygon(10,15))
    print(area_polygon(9,7))
