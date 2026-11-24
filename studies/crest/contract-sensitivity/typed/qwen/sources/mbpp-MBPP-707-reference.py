
def count_Set_Bits(n) :
    def setBits(num):
        count = 0
        while num:
            count += num & 1
            num >>= 1
        return count

    total_count = 0
    for i in range(1, n + 1):
        total_count += setBits(i)
    return total_count
