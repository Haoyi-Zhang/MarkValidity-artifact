
def find_Min_Swaps(arr, n):
	count_ones = sum(arr)
	swaps = 0
	for i in range(n):
		if arr[i] == 1:
			count_ones -= 1
		else:
			swaps += count_ones
	return swaps
