def  pair_wise(l1):
    temp=list()
    for i in range(len(l1) - 1):
        current_element = l1[i]
        next_element = l1[i + 1]
        x=(current_element, next_element)
        temp.append(x)
    return  temp