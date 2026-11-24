def  all_Characters_Same(s) :
    n = len(s)
    for  i in  range(1,n) :
        if s[0] != s[i] :
            return  False
    return  True