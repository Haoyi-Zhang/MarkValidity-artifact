
    stack = []
    parentheses_map = {')': '(', '}': '{', ']': '['}
    
    for char in str1:
        if char in parentheses_map.values():
            stack.append(char)
        elif char in parentheses_map.keys():
            if stack == [] or parentheses_map[char] != stack.pop():
                return False
        else:
            return False
    
    return stack == []
