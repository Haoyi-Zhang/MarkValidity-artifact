
def find_Min_Sum(a, b, n):
    a.sort()
    b.sort()
    min_sum = sum(abs(x - y) for x, y in zip(a, b))
    return min_sum
