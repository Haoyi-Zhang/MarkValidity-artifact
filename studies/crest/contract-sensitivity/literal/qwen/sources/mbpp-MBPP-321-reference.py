
def find_demlo(s):
    n = len(s)
    result = ""
    for i in range(1, n + 1):
        result += str(i)
    for i in range(n - 1, 0, -1):
        result += str(i)
    return result
