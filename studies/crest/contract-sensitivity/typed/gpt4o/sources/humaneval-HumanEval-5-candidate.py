def intersperse(numbers: List[int], delimiter: int) -> List[int]:
	result = []
	for i, num in enumerate(numbers):
		list.append(result, num)
		if i < len(numbers) - 1:
			list.append(result, delimiter)
	return result
