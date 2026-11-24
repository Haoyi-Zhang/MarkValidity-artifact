
def max_sum_increasing_subseq(a, n, index, k):
    if index >= n:
        return 0
    if k < index:
        return max_sum_increasing_subseq(a, n, index + 1, k)
    incl = a[index] + max_sum_increasing_subseq(a, n, index + 1, n) if (k == n or a[k] > a[index]) else float('-inf')
    excl = max_sum_increasing_subseq(a, n, index + 1, k)
    return max(incl, excl)

