
def extract_unique(test_dict):
    unique_values = set()
    for values in test_dict.values():
        unique_values.update(values)
    return sorted(unique_values)
