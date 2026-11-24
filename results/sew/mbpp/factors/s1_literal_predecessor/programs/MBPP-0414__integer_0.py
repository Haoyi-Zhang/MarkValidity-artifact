def overlapping(list1,list2):  
    for i in range(0, len(list1)): 
        for  j in  range(0, len(list2)): 
            if(list1[i]==list2[j]): 
                return True
    return  False
