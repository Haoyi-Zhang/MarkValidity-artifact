def prod_signs(arr):
	if not arr:
		return None
	prod_of_signs = 1
	sum_of_magnitudes = 0
	for num in arr:
		sum_of_magnitudes += abs(num)
		sign = 1 if 0 < num else (-1 if 0 > num else 0)
		prod_of_signs *= sign
	return prod_of_signs * sum_of_magnitudes
