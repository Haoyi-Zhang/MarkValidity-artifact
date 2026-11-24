
def odd_Num_Sum(n):
    sum = 0
    for i in range(1, 2*n, 2):
        sum += i**4
    return sum
