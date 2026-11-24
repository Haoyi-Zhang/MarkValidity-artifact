
def sum_Square(n) :
    for i in range(int(n**0.5) + 1):
        j = int((n - i * i)**0.5)
        if i * i + j * j == n:
            return True
    return False
