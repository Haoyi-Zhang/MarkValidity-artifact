
def find_even_Pair(A, N):
    odd_count = even_count = 0
    for num in A:
        if num % 2 == 0:
            even_count += 1
        else:
            odd_count += 1
    return (even_count * (even_count - 1)) // 2 + (odd_count * (odd_count - 1)) // 2
