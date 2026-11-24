
def lbs(arr):
    n = len(arr)
    lis = [1] * n
    lds = [1] * n

    for i in range(1, n):
        for j in range(0, i):
            if arr[i] > arr[j]:
                lis[i] = max(lis[i], lis[j] + 1)

    for i in reversed(range(n-1)):
        for j in reversed(range(i+1, n)):
            if arr[i] > arr[j]:
                lds[i] = max(lds[i], lds[j] + 1)

    maximum = lis[0] + lds[0] - 1
    for i in range(1, n):
        maximum = max((lis[i] + lds[i] - 1), maximum)

    return maximum
