
def sort_even(l: list):
    even_indices_values = [l[i] for i in range(0, len(l), 2)]
    even_indices_values.sort()
    l_prime = l[:]
    for idx, value in zip(range(0, len(l), 2), even_indices_values):
        l_prime[idx] = value
    return l_prime
