
def count_bidirectional(test_list):
    seen = set()
    count = 0
    for a, b in test_list:
        if (b, a) in seen:
            count += 1
        else:
            seen.add((a, b))
    return str(count)
