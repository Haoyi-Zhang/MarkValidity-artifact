
def even_Power_Sum(n):
    total = 0
    for i in range(1, n + 1):
        even_number = 2 * i
        total += even_number ** 4
    return total
