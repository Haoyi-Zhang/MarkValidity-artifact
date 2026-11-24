
def remove_dirty_chars(string, second_string):
    result = ''.join([char for char in string if char not in second_string])
    return result
