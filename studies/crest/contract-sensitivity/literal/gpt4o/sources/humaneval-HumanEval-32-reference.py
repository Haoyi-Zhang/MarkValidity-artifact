def find_zero(xs: list):
    if len(xs) % 2 != 0 or xs[-1] == 0:
        raise ValueError("Invalid list of coefficients")
    f = lambda x: poly(xs, x)
    a, b = -1e5, 1e5
    while b - a > 1e-6:
        c = (a + b) / 2
        if f(c) == 0:
            return c
        elif f(a) * f(c) < 0:
            b = c
        else:
            a = c
    return (a + b) / 2