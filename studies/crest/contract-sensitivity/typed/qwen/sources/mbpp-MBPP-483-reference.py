
def first_Factorial_Divisible_Number(x):
    factorial = 1
    for i in range(1, x + 1):
        factorial *= i
        if factorial % x == 0:
            return i
