def rearrange_bigger(n):
	nums = list(str(n))
	for i in range(len(nums) - 2, -1, -1):
		if nums[i] < nums[i + 1]:
			z = nums[i:]
			y = min(filter(lambda x: z[0] < x, z))
			z.remove(y)
			z = sorted(z)
			nums[i:] = [y] + z
			return int(str.join("", nums))
	return False
