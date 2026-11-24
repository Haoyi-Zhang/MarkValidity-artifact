def find_First_Missing(array, start, end):
	if start > end:
		return 1 + end
	if array[start] != start:
		return start
	mid = (start + end) // 2
	if array[mid] == mid:
		return find_First_Missing(array, mid + 1, end)
	return find_First_Missing(array, start, mid)
