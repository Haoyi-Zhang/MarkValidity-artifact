
def dealnnoy_num(n, m):
    if n == 0 and m == 0:
        return 1
    if n == 0:
        return dealnnoy_num(n, m - 1) + dealnnoy_num(n, m - 2)
    if m == 0:
        return dealnnoy_num(n - 1, m) + dealnnoy_num(n - 2, m)
    return dealnnoy_num(n - 1, m) + dealnnoy_num(n - 1, m - 1) + dealnnoy_num(n, m - 1)
