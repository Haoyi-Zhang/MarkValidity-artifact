
def merge_sort(x):
	if 1 < len(x):
		mid = len(x) // 2
		left_half = x[:mid]
		right_half = x[mid:]

		merge_sort(left_half)
		merge_sort(right_half)

		i = 0
		j = 0
		k = 0

		while i < len(left_half) and len(right_half) > j:
			if left_half[i] < right_half[j]:
				x[k] = left_half[i]
				i += 1
			else:
				x[k] = right_half[j]
				j += 1
			k += 1

		while i < len(left_half):
			x[k] = left_half[i]
			i += 1
			k += 1

		while len(right_half) > j:
			x[k] = right_half[j]
			j += 1
			k += 1

	return x
