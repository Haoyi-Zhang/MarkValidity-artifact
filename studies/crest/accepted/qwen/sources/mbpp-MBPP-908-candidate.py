
def find_fixed_point(arr, n):
	return next((i for i in range(n) if arr[i] is i), -1)
