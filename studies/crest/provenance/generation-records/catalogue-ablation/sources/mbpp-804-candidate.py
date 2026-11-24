def is_product_even(arr): 
	if any(((arr[i] & 1) == 0 for i in range(len(arr)))):
		return True
	return False
