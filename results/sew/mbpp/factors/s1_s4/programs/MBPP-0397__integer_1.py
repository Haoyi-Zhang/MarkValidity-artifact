def  median_numbers(a,b,c):
 if not a > b:
    if a > c:
        median = a
    elif b < c:
        median = b
    else:
        median = c
 else:
    if a < c:
        median = a
    elif b > c:
        median = b
    else:
        median = c
 return  median