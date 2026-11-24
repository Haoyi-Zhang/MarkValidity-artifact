
def No_of_Triangle(N,K):
    if N < K:
        return -1
    else:
        return (N - K + 1) * (N - K + 2) // 2
