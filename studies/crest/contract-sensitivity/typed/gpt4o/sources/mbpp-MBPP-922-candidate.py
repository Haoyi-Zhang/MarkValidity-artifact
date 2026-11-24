def max_product(arr):
	if 2 > len(arr):
		return None
	max1 = max2 = float('-inf')
	min1 = min2 = float('inf')
	for num in arr:
		if max1 < num:
			max2 = max1
			max1 = num
		else:
			max2 = max(max2, num)
		if min1 > num:
			min2 = min1
			min1 = num
		else:
			min2 = min(min2, num)
	if max2 * max1 > min1 * min2:
		return (max1, max2)
	return (min1, min2)
