
    if len(s) == 0:
        return 0
    
    min_length = float('inf')
    
    for char in set(s):
        new_s = s.replace(char, '')
        min_length = min(min_length, len(new_s))
    
    return min_length
