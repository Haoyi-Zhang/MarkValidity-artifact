
def min_Num(arr, n):
	total_sum = sum(arr)
	if total_sum % 2 == 0:
		return 0
	return next((1 for num in arr if (total_sum - num) % 2 == 0), 2)
