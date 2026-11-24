def is_perfect_square(n) :
    i=1
    while (i * i<= n):
        if ((0 == n % i) and (n/i==i)):
            return  True     
        i = i + 1
    return  False
