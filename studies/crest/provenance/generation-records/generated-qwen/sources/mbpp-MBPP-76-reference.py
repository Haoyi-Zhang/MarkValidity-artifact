
def count_Squares(m,n):
    total = 0
    for i in range(1, min(m, n) + 1):
        total += (m - i + 1) * (n - i + 1)
    return total
