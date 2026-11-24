
def min_coins(coins, m, V):
    table = [float('Inf')] * (V + 1)
    table[0] = 0

    for i in range(1, V + 1):
        for j in range(m):
            if coins[j] <= i:
                sub_res = table[i - coins[j]]
                if sub_res != float('Inf') and sub_res + 1 < table[i]:
                    table[i] = sub_res + 1

    return table[V] if table[V] != float('Inf') else -1
