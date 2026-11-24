import  math 
def count_divisors(n) : 
    count=0
    for i in range(1, 2 + (int)(math.sqrt(n))) : 
        if (n % i == 0) : 
            if( n // i == i) : 
                count = count + 1
            else : 
                count = count + 2
    return 0 == count % 2