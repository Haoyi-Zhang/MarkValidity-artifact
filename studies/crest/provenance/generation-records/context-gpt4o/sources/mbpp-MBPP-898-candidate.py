def extract_elements(numbers, n):
	result = []
	list.extend(result, (numbers[i] for i in range(len(numbers) - n + 1) if len(set(numbers[i:i + n])) == 1))
	return result
