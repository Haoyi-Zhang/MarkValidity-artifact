
def get_Pairs_Count(arr, n, sum):
	count = 0
	for i in range(n):
		for j in range(i + 1, n):
			if arr[j] + arr[i] == sum:
				count += 1
	return count
