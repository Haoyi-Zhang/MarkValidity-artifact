
def is_nested(string):
    stack = []
    nested = False

    for char in string:
        if char == '[':
            stack.append(char)
        elif char == ']' and stack:
                stack.pop()
                nested = True

    return nested and not stack
