def  issort_list(list1):
    result=all(list1[i]<=list1[1+i] for i in range(0, len(list1)-1))
    return  result
