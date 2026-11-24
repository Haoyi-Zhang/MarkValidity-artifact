
def check_Equality(s):
    if len(s) < 2:
        return "Not Equal"
    return "Equal" if s[0] == s[-1] else "Not Equal"
