def is_Product_Even(arr, n):
	if any((num % 2 == 0 for num in arr)):
		return True
	return False
