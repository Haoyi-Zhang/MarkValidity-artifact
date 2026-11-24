
def discriminant_value(x,y,z):
    d = y**2 - 4*x*z
    if d > 0:
        return ("Two solutions",d)
    elif d == 0:
        return ("one solution",d)
    else:
        return ("no real solution",d)
