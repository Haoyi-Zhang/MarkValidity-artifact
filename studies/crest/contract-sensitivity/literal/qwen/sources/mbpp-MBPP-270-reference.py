
def sum_even_and_even_index(arr, n):
    total = 0
    for i in range(0, n, 2):
        if arr[i] % 2 == 0:
            total += arr[i]
    return total
