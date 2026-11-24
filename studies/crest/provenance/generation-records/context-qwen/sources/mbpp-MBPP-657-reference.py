
def first_Digit(n) :
    fact = 1
    for i in range(2, n + 1) :
        fact *= i
 
    while (fact % 10 == 0) :
        fact //= 10
     
    while (fact >= 10) :
        fact //= 10
     
    return int(fact)
