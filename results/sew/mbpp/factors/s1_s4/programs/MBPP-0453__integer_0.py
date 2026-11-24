import  math 
def  sumofFactors(n) : 
    if (0 != n % 2) : 
        return  0
    res = 1
    for i in range(2, 1 + (int)(math.sqrt(n))) :    
        count = 0
        curr_sum = 1
        curr_term = 1
        while  (n % i == 0) : 
            count= count + 1
            n = n // i 
            if (2 == i and 1 == count) : 
                curr_sum=0
            curr_term = curr_term * i 
            curr_sum = curr_sum + curr_term 
        res = curr_sum * res  
    if (n>=2) : 
        res = res * (n + 1) 
    return  res
