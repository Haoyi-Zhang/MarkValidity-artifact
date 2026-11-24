
def decimal_To_Binary(N):
    if N == 0:
        return 0
    binary = ""
    while N > 0:
        binary = str(N % 2) + binary
        N = N // 2
    return int(binary)
