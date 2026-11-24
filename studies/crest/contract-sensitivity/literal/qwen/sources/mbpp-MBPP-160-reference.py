
def solution(a, b, n):
    for x in range(n // a + 1):
        if (n - a * x) % b == 0:
            y = (n - a * x) // b
            return ('x = ', x, ', y = ', y)
    return 'No solution'
