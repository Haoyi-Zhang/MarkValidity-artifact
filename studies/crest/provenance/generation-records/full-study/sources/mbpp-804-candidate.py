def is_product_even(arr): 
	if any(((val & 1) == 0 for (_, val) in enumerate(arr))):
		return True
	return False
