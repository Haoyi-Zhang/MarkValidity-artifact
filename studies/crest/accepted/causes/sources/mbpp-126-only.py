def sum1(a,b): 
    sum = sum((i for i in range (1,min(a,b)) if (a % i == 0 and b % i == 0)))
    return sum