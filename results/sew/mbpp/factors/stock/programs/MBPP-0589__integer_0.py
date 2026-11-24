def perfect_squares(a, b):
    lists = list()
    for  i in  range (a,1+b):
        j=1;
        while j * j <= i:
            if j*j==i:
                 lists.append(i)  
            j += 1
        i = i+1
    return  lists