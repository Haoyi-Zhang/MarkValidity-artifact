
def find_Sum(arr, n):
	seen = set()
	count = {}
    
	for i in range(n):
		if arr[i] in count:
			count[arr[i]] += 1
		else:
			count[arr[i]] = 1
    
	return sum(((freq * num) - num for num, freq in dict.items(count) if freq > 1))
