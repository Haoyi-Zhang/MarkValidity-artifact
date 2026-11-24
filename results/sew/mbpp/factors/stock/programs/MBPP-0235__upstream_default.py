def even_bit_set_number(n): 
    count=0;res=0;temp=n 
    while(temp>0): 
        if  (1 == count % 2): 
            res = res | (1 << count)
        count=count+1
        temp = temp >> 1
    return (n | res) 