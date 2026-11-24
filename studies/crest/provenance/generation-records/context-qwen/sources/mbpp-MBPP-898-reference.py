
    result = []
    count = 1
    for i in range(1, len(numbers)):
        if numbers[i] == numbers[i - 1]:
            count += 1
        else:
            if count >= n:
                result.append(numbers[i - 1])
            count = 1
    if count >= n:
        result.append(numbers[-1])
    return result
