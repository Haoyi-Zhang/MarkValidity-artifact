
def count_reverse_pairs(test_list):
    count = 0
    seen = set()
    for word in test_list:
        reverse_word = word[::-1]
        if reverse_word in seen:
            count += 1
        seen.add(word)
    return str(count)
