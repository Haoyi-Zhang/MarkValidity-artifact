def f(n):
    def factorial(num):
        result = 1
        for i in range(1, num + 1):
            result *= i
        return result

    def sum_to(num):
        return num * (num + 1) // 2

    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:
            result.append(factorial(i))
        else:
            result.append(sum_to(i))
    return result