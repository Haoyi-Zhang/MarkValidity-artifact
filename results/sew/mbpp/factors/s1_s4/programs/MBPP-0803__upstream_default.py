def  is_perfect_square(n) :
    i = 1
    while  (i * i<= n):
        if  ((n % i == 0) and  (n / i == i)):
            return  True     
        i=1 + i
    return  False