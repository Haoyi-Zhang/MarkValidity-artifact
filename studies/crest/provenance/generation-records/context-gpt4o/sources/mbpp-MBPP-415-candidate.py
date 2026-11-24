def max_Product(arr):
	max1 = 0
	max2 = 0
	min1 = 0
	min2 = 0
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
		return (max2, max1)
	return (min2, min1)
