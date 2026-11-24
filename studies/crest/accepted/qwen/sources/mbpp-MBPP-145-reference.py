
    if n < 2:
        return 0
    min_element = arr[0]
    max_element = arr[0]
    for i in range(1, n):
        min_element = min(min_element, arr[i])
        max_element = max(max_element, arr[i])
    return abs(max_element - min_element)
