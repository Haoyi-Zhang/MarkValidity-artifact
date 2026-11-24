
def Sum_of_Inverse_Divisors(N, Sum):
    total = 0
    for i in range(1, N + 1):
        if Sum % i == 0:
            total += 1 / i
    return total
