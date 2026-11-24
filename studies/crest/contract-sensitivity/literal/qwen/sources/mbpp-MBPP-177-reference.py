
def answer(L, R):
    if L == 1:
        return (1, 2)
    for i in range(L, R + 1):
        for j in range(i + 1, R + 1):
            if (i * j) // math.gcd(i, j) <= R:
                return (i, j)
