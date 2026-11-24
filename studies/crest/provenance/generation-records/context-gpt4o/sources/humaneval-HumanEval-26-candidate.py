def remove_duplicates(numbers: List[int]) -> List[int]:
	seen = set()
	duplicates = set()
	for number in numbers:
		if number in seen:
			set.add(duplicates, number)
		else:
			set.add(seen, number)
	return [number for number in numbers if number not in duplicates]
