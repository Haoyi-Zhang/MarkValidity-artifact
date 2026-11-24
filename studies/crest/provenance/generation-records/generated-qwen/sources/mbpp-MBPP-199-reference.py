
def highest_Power_of_2(n):
    if n == 0:
        return 0
    power = 1
    while power <= n:
        power = power << 1
    return power >> 1
