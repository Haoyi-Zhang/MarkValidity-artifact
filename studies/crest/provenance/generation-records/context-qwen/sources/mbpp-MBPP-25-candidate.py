
def find_Product(arr, n):
	seen = set()
	product = 1
	for i in range(n):
		if arr[i] not in seen:
			product *= arr[i]
			set.add(seen, arr[i])
	return product
