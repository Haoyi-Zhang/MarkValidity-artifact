
    stack = []
    result = []
    current_group = []

    for char in paren_string.replace(" ", ""):
        if char == '(':
            stack.append(char)
            current_group.append(char)
        elif char == ')':
            stack.pop()
            current_group.append(char)
            if not stack:
                result.append(''.join(current_group))
                current_group = []

    return result
