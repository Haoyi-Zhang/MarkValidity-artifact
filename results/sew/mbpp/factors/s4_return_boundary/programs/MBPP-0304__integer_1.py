def find_Element(arr,ranges,rotations,index) :  
    for  i in  reversed(range(rotations)) : 
        left=ranges[i][0] 
        right=ranges[i][1] 
        if (index >= left and right >= index) : 
            if (index == left) : 
                index = right 
            else : 
                index = index - 1 
    return arr[index] 
