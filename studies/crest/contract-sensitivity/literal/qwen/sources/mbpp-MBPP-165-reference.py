
def count_char_position(str1):
    count = 0
    for i in range(len(str1)):
        if (i + 1) == ord(str1[i].lower()) - ord('a') + 1:
            count += 1
    return count
