
    i = j = 0
    while i < m and j < n:
        if arr1[i] < arr2[j]:
            k -= 1
            if k == 0:
                return arr1[i]
            i += 1
        else:
            k -= 1
            if k == 0:
                return arr2[j]
            j += 1
    
    while i < m:
        k -= 1
        if k == 0:
            return arr1[i]
        i += 1
    
    while j < n:
        k -= 1
        if k == 0:
            return arr2[j]
        j += 1

