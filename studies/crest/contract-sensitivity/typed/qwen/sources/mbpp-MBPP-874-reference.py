
def check_Concat(str1, str2):
    if len(str1) % len(str2) != 0:
        return False
    for i in range(0, len(str1), len(str2)):
        if str1[i:i+len(str2)] != str2:
            return False
    return True
