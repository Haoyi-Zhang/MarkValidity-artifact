
def check_expression(exp):
    stack = []
    matching_bracket = {')': '(', '}': '{', ']': '['}
    
    for char in exp:
        if char in matching_bracket.values():
            stack.append(char)
        elif char in matching_bracket.keys():
            if stack == [] or matching_bracket[char] != stack.pop():
                return False
    
    return stack == []
