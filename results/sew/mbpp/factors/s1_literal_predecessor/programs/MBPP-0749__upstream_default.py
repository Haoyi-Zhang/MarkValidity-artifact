def  sort_numeric_strings(nums_str):
    result = []
    for x in nums_str:
        result.append(int(x))
    result.sort()
    return  result
