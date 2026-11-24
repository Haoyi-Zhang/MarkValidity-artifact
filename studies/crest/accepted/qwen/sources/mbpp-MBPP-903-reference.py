
def count_Unset_Bits(n) :
    def count_unset_bits_in_number(x):
        count = 0
        while x:
            count += x & 1 == 0
            x >>= 1
        return count

    total_unset_bits = 0
    for i in range(1, n + 1):
        total_unset_bits += count_unset_bits_in_number(i)

    return total_unset_bits
