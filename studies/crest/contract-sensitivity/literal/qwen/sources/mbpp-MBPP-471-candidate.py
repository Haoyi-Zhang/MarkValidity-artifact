
def find_remainder(arr, lens, n):
	result = 1
	for i in range(lens):
		result = (result * arr[i]) % n
	return result
