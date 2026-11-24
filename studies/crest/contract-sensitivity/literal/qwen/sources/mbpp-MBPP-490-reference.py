
def extract_symmetric(test_list):
    seen = set()
    result = set()
    for pair in test_list:
        if pair[::-1] in seen:
            result.add(pair)
        seen.add(pair)
    return result
