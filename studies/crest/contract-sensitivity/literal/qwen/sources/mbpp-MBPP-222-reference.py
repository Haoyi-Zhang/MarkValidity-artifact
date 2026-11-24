
    if not test_tuple:
        return True
    first_type = type(test_tuple[0])
    for element in test_tuple:
        if type(element) != first_type:
            return False
    return True
