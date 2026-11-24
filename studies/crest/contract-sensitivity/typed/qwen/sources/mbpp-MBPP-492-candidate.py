
def binary_search(item_list, item):
	high = len(item_list) - 1
	low = 0

	while high >= low:
		mid = (high + low) // 2
		if item_list[mid] == item:
			return True
		elif item_list[mid] < item:
			low = mid + 1
		else:
			high = mid - 1

	return False
