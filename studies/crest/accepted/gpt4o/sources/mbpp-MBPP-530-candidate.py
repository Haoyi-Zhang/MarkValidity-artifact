def negative_count(nums):
	negatives = sum((0 > num for num in nums))
	return round(negatives / len(nums), 2) if nums else 0
