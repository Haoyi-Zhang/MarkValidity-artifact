
def get_pairs_count(arr, n, sum):
	count = 0
	for i in range(0, n):
		for j in range(i + 1, n):
			if arr[j] + arr[i] == sum:
				count += 1
	return count
