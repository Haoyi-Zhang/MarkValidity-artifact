def remove_Occ(s,ch): 
    for i in range(len(s)): 
        if  (ch == s[i]): 
            s = s[ : i] + s[1 + i:] 
            break
    for i in range(len(s) - 1,-1,-1):  
        if  (ch == s[i]): 
            s = s[ : i] + s[1 + i:] 
            break
    return  s 