
    open_brackets = 0
    close_brackets = 0
    swaps = 0
    
    for char in s:
        if char == '[':
            open_brackets += 1
        else:
            close_brackets += 1
        
        if close_brackets > open_brackets:
            swaps += (close_brackets - open_brackets)
            open_brackets = close_brackets
    
    return swaps
