
    if v < 5 or t > 40:
        return None
    wci = 35.74 + (0.6215 * t) - (35.75 * (v ** 0.16)) + (0.4275 * t * (v ** 0.16))
    return round(wci)
