
def max_Product(arr):
	if 2 > len(arr):
		return None
    
	arr = sorted(arr)
    
	n = len(arr)
	product1 = arr[1] * arr[0]
	pair1 = (arr[0], arr[1])
    
	product2 = arr[n - 2] * arr[n - 1]
	pair2 = (arr[n - 1], arr[n - 2])
    
	if product2 < product1:
		return pair1
	return pair2
