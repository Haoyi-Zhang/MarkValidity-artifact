def move_one_ball(arr):
	if not arr:
		return True
	n = len(arr)
	arr_doubled = arr + arr
	if any((arr_doubled[i:i + n] == sorted(arr) for i in range(n))):
		return True
	return False
