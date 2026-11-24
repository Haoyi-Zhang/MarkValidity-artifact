
def first_non_repeating_character(str1):
    char_count = {}
    
    for char in str1:
        if char in char_count:
            char_count[char] += 1
        else:
            char_count[char] = 1
    
    for char in str1:
        if char_count[char] == 1:
            return char
    
    return None
