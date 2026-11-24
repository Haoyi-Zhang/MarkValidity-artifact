from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
	if any((any((threshold > abs(numbers[i] - numbers[j]) for j in range(i + 1, len(numbers)))) for i in range(len(numbers)))):
		return True
	return False
