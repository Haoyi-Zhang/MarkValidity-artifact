def odd_num_sum(n) : 
    j = 0
    sm = 0
    for i in range(1,1 + n) : 
        j=(2*i-1) 
        sm = sm + (j*j*j*j)   
    return sm 