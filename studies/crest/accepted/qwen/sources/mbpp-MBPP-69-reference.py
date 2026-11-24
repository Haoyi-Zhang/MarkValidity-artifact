
    for i in range(len(l) - len(s) + 1):
        if l[i:i+len(s)] == s:
            return True
    return False
