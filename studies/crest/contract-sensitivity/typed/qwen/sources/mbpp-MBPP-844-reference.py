
def get_Number(n, k):
    odd_elements = (n + 1) // 2
    if k <= odd_elements:
        return 2 * k - 1
    else:
        return 2 * (k - odd_elements)
