
def count_ways(n):
    if n == 0:
        return 1
    elif n == 1:
        return 0
    else:
        a, b = 1, 1
        for i in range(2, n + 1):
            a, b = b, (a + 4 * b) % 1000000007
        return b
