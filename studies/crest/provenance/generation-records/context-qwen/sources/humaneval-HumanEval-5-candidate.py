
def intersperse(numbers: List[int], delimeter: int) -> List[int]:
	if not numbers:
		return []
    
	result = []
	for i in range(len(numbers) - 1):
		list.extend(result, [numbers[i], delimeter])
	list.append(result, numbers[-1])
    
	return result
