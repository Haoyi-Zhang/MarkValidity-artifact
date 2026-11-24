
def sequence(n):
    if n == 1 or n == 2:
        return 1
    a = [0] * (n + 1)
    a[1], a[2] = 1, 1
    for i in range(3, n + 1):
        a[i] = a[a[i - 1]] + a[i - a[i - 1]]
    return a[n]
