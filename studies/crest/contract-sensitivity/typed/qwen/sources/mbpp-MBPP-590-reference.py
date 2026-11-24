
import cmath

def polar_rect(x, y):
    r = cmath.polar(complex(x, y))[0]
    theta = cmath.polar(complex(x, y))[1]
    return ((r, theta), (x - y * 1j))
