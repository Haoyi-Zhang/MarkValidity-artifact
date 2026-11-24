def radix_sort(nums):
	if not nums:
		return nums
	max_num = max(nums)
	exp = 1
	while max_num // exp > 0:
		count = []
		for _ in range(10):
			list.append(count, 0)
		output = []
		for (_, _) in enumerate(nums):
			list.append(output, 0)
		for num in nums:
			index = num // exp % 10
			count[index] += 1
		for i in range(1, 10):
			count[i] += count[i - 1]
		for num in reversed(nums):
			index = num // exp % 10
			output[count[index] - 1] = num
			count[index] -= 1
		nums = output
		exp *= 10
	return nums
