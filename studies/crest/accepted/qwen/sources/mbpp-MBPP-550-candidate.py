
def find_Max(arr, low, high):
	if low == high:
		return arr[low]
    
	mid = (high - low) // 2 + low
    
	if arr[mid] > arr[mid + 1]:
		return arr[mid]
    
	if arr[mid] < arr[mid + 1]:
		return find_Max(arr, mid + 1, high)
    
	return find_Max(arr, low, mid)
