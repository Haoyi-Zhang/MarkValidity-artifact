
def smallest_missing(A, left_element, right_element):
    for i in range(left_element, right_element + 1):
        if i not in A:
            return i
    return right_element + 1
