def get_max_triples(n):
    a = [i * i - i + 1 for i in range(1, n + 1)]
    triple_count = 0

    mod_map = {0: 0, 1: 0, 2: 0}

    for num in a:
        mod_map[num % 3] += 1

    triple_count += (mod_map[0] * (mod_map[0] - 1) * (mod_map[0] - 2)) // 6
    triple_count += (mod_map[1] * (mod_map[1] - 1) * (mod_map[1] - 2)) // 6
    triple_count += (mod_map[2] * (mod_map[2] - 1) * (mod_map[2] - 2)) // 6

    triple_count += mod_map[0] * mod_map[1] * mod_map[2]

    return triple_count