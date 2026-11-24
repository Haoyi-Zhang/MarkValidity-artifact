def  find_Rotations(str): 
    tmp, n = str + str, len(str) 
    for  i in  range(1,1 + n): 
        substring=tmp[i: n+i] 
        if (str == substring): 
            return  i 
    return  n 