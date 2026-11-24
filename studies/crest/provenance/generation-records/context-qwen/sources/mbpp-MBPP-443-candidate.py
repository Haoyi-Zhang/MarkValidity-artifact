
def largest_neg(list1):
	neg_numbers = [num for num in list1 if 0 > num]
	return max(neg_numbers) if neg_numbers else None
