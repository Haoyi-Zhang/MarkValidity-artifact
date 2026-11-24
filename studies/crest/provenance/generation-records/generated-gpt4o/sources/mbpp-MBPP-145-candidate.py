def max_Abs_Diff(arr, n):
	max_element = arr[0]
	min_element = arr[0]
	for i in range(1, n):
		max_element = max(max_element, arr[i])
		min_element = min(min_element, arr[i])
	return max_element - min_element


print(max_Abs_Diff((2, 1, 5, 3), 4))
print(max_Abs_Diff((9, 3, 2, 5, 1), 5))
print(max_Abs_Diff((3, 2, 1), 3))
