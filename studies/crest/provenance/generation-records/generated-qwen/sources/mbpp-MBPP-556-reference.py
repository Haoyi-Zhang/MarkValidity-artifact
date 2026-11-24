
def find_Odd_Pair(A, N):
    odd_count = sum(1 for x in A if x & 1)
    even_count = N - odd_count
    return odd_count * even_count + odd_count * (odd_count - 1) // 2
