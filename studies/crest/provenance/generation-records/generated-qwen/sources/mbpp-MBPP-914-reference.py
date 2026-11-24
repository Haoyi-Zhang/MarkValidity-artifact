
def is_Two_Alter(s):
    if len(set(s)) != 2:
        return False
    for i in range(2, len(s)):
        if s[i] != s[i % 2]:
            return False
    return True
