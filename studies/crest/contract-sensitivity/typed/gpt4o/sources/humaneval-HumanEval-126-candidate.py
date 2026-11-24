def is_sorted(lst):
	if 1 >= len(lst):
		return True
	if any((lst[i] < lst[i - 1] for i in range(1, len(lst)))):
		return False
	counts = {}
	for num in lst:
		if num in counts:
			counts[num] += 1
			if 2 < counts[num]:
				return False
		else:
			counts[num] = 1
	return True
