
def cube_Sum(n):
    sum = 0
    for i in range(1, n + 1):
        even_num = i * 2
        sum += even_num ** 3
    return sum
