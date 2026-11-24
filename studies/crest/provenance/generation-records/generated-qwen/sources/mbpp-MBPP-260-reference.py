
def newman_prime(n):
    def nsw_number(k):
        if k == 0:
            return 1
        elif k == 1:
            return 1
        else:
            return 2 * nsw_number(k - 1) + nsw_number(k - 2)
    
    count = 0
    i = 0
    while True:
        candidate = nsw_number(i)
        if all(candidate % j != 0 for j in range(2, int(candidate ** 0.5) + 1)):
            count += 1
            if count == n:
                return candidate
        i += 1
