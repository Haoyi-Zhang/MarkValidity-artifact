
def count_self_modular_inverses(arr, N, P):
    count = 0
    for i in range(N):
        if (arr[i] * arr[i]) % P == 1:
            count += 1
    return count

# Test cases
print(count_self_modular_inverses([1, 6, 4, 5], 4, 7))  # Output: 2
print(count_self_modular_inverses([1, 3, 8, 12, 12], 5, 13))  # Output: 3
print(count_self_modular_inverses([2, 3, 4, 5], 4, 6))  # Output: 1
