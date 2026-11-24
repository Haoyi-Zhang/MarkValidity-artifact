def mean_absolute_deviation(numbers: List[float]) -> float:
	mean_value = sum(numbers) / len(numbers)
	deviations = [abs(x - mean_value) for x in numbers]
	return sum(deviations) / len(numbers)
