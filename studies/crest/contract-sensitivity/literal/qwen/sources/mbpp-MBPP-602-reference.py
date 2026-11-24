
    char_set = set()
    for char in str1:
        if char in char_set:
            return char
        else:
            char_set.add(char)
    return "None"
