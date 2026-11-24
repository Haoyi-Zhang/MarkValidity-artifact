
    # Get the size of the list
    size = len(newList)
    
    # Swap the first and last element
    temp = newList[0]
    newList[0] = newList[size - 1]
    newList[size - 1] = temp
    
    return newList
