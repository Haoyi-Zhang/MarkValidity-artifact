
    if not lists:
        return ([], [])
    
    unique_elements = []
    counts = []
    count = 1
    
    for i in range(1, len(lists)):
        if lists[i] == lists[i - 1]:
            count += 1
        else:
            unique_elements.append(lists[i - 1])
            counts.append(count)
            count = 1
            
    unique_elements.append(lists[-1])
    counts.append(count)
    
    return (unique_elements, counts)
