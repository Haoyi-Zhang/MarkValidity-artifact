
def sum_three_smallest_nums(lst):
	positive_nums = [num for num in lst if 0 < num]
	positive_nums = sorted(positive_nums)
	return sum(positive_nums[:3])
