
def length_Of_Last_Word(a):
    if not a.strip():
        return 0
    words = a.split()
    return len(words[-1])
