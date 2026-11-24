
import math

def prod_Square(n):
    for i in range(int(math.sqrt(n)) + 1):
        if n % (i * i) == 0:
            m = n // (i * i)
            j = int(math.sqrt(m))
            if j * j == m:
                return True
    return False
