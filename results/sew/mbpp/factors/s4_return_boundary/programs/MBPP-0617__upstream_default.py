def  min_Jumps(steps, d): 
    (a, b) = steps
    temp = a 
    a = min(a, b) 
    b = max(temp, b) 
    if (d >= b): 
        return  (d + b - 1) / b 
    if (d == 0): 
        return  0
    if not (d == a): 
        return 2
    else:
        return 1
