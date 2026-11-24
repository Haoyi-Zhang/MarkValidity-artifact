
    result = []
    previous_char = None
    for c in string:
        if c != char or c != previous_char:
            result.append(c)
            previous_char = c
    return ''.join(result)
