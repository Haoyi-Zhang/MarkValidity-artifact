
def count_Pairs(arr, n):
    from collections import Counter
    count = 0
    freq = Counter(arr)
    for val in freq.values():
        if val > 1:
            count += val * (val - 1) // 2
    return count
