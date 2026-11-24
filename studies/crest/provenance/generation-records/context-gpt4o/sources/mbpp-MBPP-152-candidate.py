def merge_sort(x):
	if 1 >= len(x):
		return x
	mid = len(x) // 2
	left = merge_sort(x[:mid])
	right = merge_sort(x[mid:])
	return merge(left, right)


def merge(left, right):
	left_index = 0
	right_index = 0
	sorted_list = []
	while left_index < len(left) and len(right) > right_index:
		if right[right_index] > left[left_index]:
			list.append(sorted_list, left[left_index])
			left_index += 1
		else:
			list.append(sorted_list, right[right_index])
			right_index += 1
	list.extend(sorted_list, left[left_index:])
	list.extend(sorted_list, right[right_index:])
	return sorted_list
