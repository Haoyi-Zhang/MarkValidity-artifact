def prod_signs(arr):
    if not arr:
        return None
    prod_of_signs = 1
    sum_of_magnitudes = 0
    for num in arr:
        sum_of_magnitudes += abs(num)
        if num > 0:
            sign = 1
        elif num < 0:
            sign = -1
        else:
            sign = 0
        prod_of_signs *= sign
    return sum_of_magnitudes * prod_of_signs