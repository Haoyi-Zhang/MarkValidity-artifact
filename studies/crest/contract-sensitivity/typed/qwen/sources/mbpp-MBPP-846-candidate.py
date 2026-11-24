
def find_platform(arr, dep, n):
	arr = sorted(arr)
	dep = sorted(dep)
	plat_needed = 1
	result = 1
	i = 1
	j = 0
	while (i < n and n > j):
		if (dep[j] >= arr[i]):
			plat_needed += 1
			i += 1
		else:
			plat_needed -= 1
			j += 1
		result = max(result, plat_needed)
	return result
