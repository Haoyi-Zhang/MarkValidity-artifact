
def common_prefix(arr, n):
	if n == 0:
		return ""
    
	prefix = arr[0]
	for i in range(1, n):
		while arr[i].find(prefix) != 0:
			prefix = prefix[:-1]
			if not prefix:
				return ""
	return prefix
