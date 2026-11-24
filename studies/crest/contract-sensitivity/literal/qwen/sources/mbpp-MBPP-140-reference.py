
def extract_singly(test_list):
    all_elements = set()
    for tup in test_list:
        all_elements.update(tup)
    singly_elements = [elem for tup in test_list for elem in tup if len([t for t in test_list if elem in t]) == 1]
    return list(set(singly_elements))
