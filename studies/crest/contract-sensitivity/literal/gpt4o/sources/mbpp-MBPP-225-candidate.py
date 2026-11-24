def find_Min(arr, low, high):
	if high < low:
		return arr[0]
	if high == low:
		return arr[low]
	mid = (high - low) // 2 + low
	if mid < high and arr[mid + 1] < arr[mid]:
		return arr[mid + 1]
	if mid > low and arr[mid - 1] > arr[mid]:
		return arr[mid]
	if arr[mid] < arr[high]:
		return find_Min(arr, low, mid - 1)
	return find_Min(arr, mid + 1, high)
