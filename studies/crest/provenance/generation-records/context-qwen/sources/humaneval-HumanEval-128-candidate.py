
def prod_signs(arr):
	if not arr:
		return None
    
	product_of_signs = 1
	sum_of_magnitudes = 0
    
	for num in arr:
		if num == 0:
			return 0
		elif 0 > num:
			product_of_signs *= -1
		sum_of_magnitudes += abs(num)
    
	return product_of_signs * sum_of_magnitudes
