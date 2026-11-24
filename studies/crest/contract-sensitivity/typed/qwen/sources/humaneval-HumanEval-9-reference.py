
def rolling_max(numbers: List[int]) -> List[int]:
    result = []
    current_max = float('-inf')
    for number in numbers:
        if number > current_max:
            current_max = number
        result.append(current_max)
    return result
