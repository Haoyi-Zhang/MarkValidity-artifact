
def lucky_num(n):
    def sieve(limit):
        is_lucky = [True] * (limit + 1)
        i = 1
        while i <= limit:
            if is_lucky[i]:
                first_lucky_offset = i
                j = i + first_lucky_offset
                while j <= limit:
                    is_lucky[j] = False
                    j += first_lucky_offset
            i += 1
        return [i for i in range(1, limit + 1) if is_lucky[i]]

    limit = 2 * n
    lucky_numbers = sieve(limit)
    while len(lucky_numbers) > n:
        limit *= 2
        lucky_numbers = sieve(limit)
    
    return lucky_numbers[:n]
