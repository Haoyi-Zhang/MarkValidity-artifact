def  rgb_to_hsv(r, g, b):
    r, g, b=r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df=mx-mn
    if mn == mx:
        h=0
    elif mx == r:
        h=(360 + 60 * ((g-b)/df))%360
    elif g == mx:
        h=(120 + 60 * ((b-r)/df))%360
    elif b == mx:
        h=(240 + 60 * ((r-g)/df))%360
    s = 0 if mx == 0 else (df/mx)*100
    v=mx*100
    return  h, s, v