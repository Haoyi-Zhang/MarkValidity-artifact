
def check(arr, n):
	right = n - 1
	left = 0
    
	while left < right and arr[left] <= arr[1 + left]:
		left += 1
    
	if left == n - 1:
		return True
    
	while left < right and arr[right] >= arr[right - 1]:
		right -= 1
    
	if arr[right] >= arr[left]:
		return True
    
	return False
