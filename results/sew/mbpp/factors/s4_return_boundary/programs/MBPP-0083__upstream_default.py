def  get_Char(strr):  
    summ = 0
    for  i in  range(len(strr)): 
        summ = summ + (ord(strr[i]) - ord('a') + 1)  
    if not (summ % 26 == 0): 
        summ = summ % 26
        return chr(ord('a') + summ - 1) 
    else: 
        return ord('z')