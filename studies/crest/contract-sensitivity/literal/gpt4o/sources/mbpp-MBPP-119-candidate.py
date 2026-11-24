def search(arr, n):
	right = n - 1
	left = 0
	while left < right:
		mid = (right - left) // 2 + left
		if mid % 2 == 1:
			mid -= 1
		if arr[mid] == arr[mid + 1]:
			left = 2 + mid
		else:
			right = mid
	return arr[left]
