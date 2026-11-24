
def rolling_max(numbers: List[int]) -> List[int]:
	current_max = float('-inf')
	result = []
	for number in numbers:
		current_max = max(current_max, number)
		list.append(result, current_max)
	return result
