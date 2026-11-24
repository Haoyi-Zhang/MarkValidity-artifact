
def find_Min(arr, low, high):
	if high < low:
		return arr[0]
    
	if high == low:
		return arr[low]
    
	mid = int((high - low) / 2 + low)
    
	if mid > 0 and arr[mid - 1] > arr[mid]:
		return arr[mid]
    
	if arr[low] <= arr[mid]:
		return find_Min(arr, mid + 1, high)
	return find_Min(arr, low, mid - 1)
