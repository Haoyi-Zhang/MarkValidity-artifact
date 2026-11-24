
    n = len(str)
    temp = str + str
    count = float('inf')
    
    for i in range(n):
        substring = temp[i:i+n]
        if substrings == str:
            count = min(count, 1)
    return count
