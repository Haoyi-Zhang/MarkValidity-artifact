
def sort_mixed_list(mixed_list):
	numbers = sorted([item for item in mixed_list if isinstance(item, int)])
	strings = sorted([item for item in mixed_list if isinstance(item, str)])
	return numbers + strings
