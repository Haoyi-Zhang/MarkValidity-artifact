def check(arr, n):
	right = n - 1
	prev = float('-inf')
	left = 0
	while left <= right:
		if arr[right] >= arr[left]:
			if arr[left] < prev:
				return False
			else:
				prev = arr[left]
				left += 1
		elif arr[right] < prev:
			return False
		else:
			prev = arr[right]
			right -= 1
	return True
