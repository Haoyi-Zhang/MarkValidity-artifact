import  math 
def sumofFactors(n) : 
    if (n % 2 != 0) : 
        return  0
    res = 1
    for  i in  range(2, (int)(math.sqrt(n)) + 1) :    
        count = 0
        curr_sum = 1
        curr_term = 1
        while (0 == n % i) : 
            count+= 1
            n //= i 
            if  (2 == i and  1 == count) : 
                curr_sum=0
            curr_term *= i 
            curr_sum += curr_term 
        res *= curr_sum  
    if (n >= 2) : 
        res *= (1 + n) 
    return  res
