
def get_max_occuring_char(str1):
    char_count = {}
    for char in str1:
        if char_count.get(char) is None:
            char_count[char] = 0
        else:
            char_count[char] += 1

    max_count = -1
    max_char = ''
    for char, count in char_count.items():
        if count > max_count:
            max_count = count
            max_char = char

    return max_char
