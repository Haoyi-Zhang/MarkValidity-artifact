
def radix_sort(nums):
	max_digit = max(nums)
	RADIX = 10
	placement = 1

	while max_digit >= placement:
		buckets = [list() for _ in range(RADIX)]
		for i in nums:
			tmp = int((i / placement) % RADIX)
			buckets[tmp].append(i)
		a = 0
		for b in range(RADIX):
			buck = buckets[b]
			for i in buck:
				nums[a] = i
				a += 1
		placement *= RADIX

	return nums
