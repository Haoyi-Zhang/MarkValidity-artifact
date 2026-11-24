
def odd_Num_Sum(n) :
    sum = 0
    for i in range(n):
        num = 2 * i + 1
        sum += num ** 5
    return sum
