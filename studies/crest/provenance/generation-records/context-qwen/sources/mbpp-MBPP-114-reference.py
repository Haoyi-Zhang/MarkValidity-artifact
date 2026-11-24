
def assign_freq(test_list):
    from collections import Counter
    freq_count = Counter(tuple(t) for t in test_list)
    result = [(t + (freq_count[t],)) for t in set(tuple(t) for t in test_list)]
    return str(result)
