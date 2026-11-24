def find_platform(arr, dep, n):
	arr = sorted(arr)
	dep = sorted(dep)
	i = 1
	j = 0
	platform_needed = 1
	result = 1
	while i < n and n > j:
		if dep[j] >= arr[i]:
			platform_needed += 1
			i += 1
		else:
			platform_needed -= 1
			j += 1
		result = max(result, platform_needed)
	return result
