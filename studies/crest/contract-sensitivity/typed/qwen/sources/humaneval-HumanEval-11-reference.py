
    if len(a) != len(b):
        raise ValueError("Input strings must be of equal length")
    
    result = []
    for i in range(len(a)):
        if a[i] == b[i]:
            result.append('0')
        else:
            result.append('1')
    
    return ''.join(result)
