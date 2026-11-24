def check_min_heap_helper(arr, i):
	if i * 2 + 2 > len(arr):
		return True
	left_child = (arr[i] <= arr[i * 2 + 1]) and check_min_heap_helper(arr, i * 2 + 1)
	right_child = (i * 2 + 2 == len(arr)) or (arr[i] <= arr[i * 2 + 2] 
                                      and check_min_heap_helper(arr, i * 2 + 2))
	return left_child and right_child


def check_min_heap(arr):
	return check_min_heap_helper(arr, 0)
