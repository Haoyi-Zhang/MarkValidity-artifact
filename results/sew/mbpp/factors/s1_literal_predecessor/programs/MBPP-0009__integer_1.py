def  find_Rotations(str): 
    tmp = str + str
    n = len(str) 
    for i in range(1,n + 1): 
        substring=tmp[i: i+n] 
        if  (substring == str): 
            return  i 
    return n 