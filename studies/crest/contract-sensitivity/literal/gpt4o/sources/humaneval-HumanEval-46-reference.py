def fib4(n: int):
    if n < 0:
        return None
    if n in [0, 1]:
        return 0
    if n == 2:
        return 2
    if n == 3:
        return 0
    fib_sequence = [0, 0, 2, 0]
    for i in range(4, n + 1):
        next_value = sum(fib_sequence)
        fib_sequence.pop(0)
        fib_sequence.append(next_value)
    return fib_sequence[-1]