
def find_first_duplicate(nums):
	seen = set()
	for num in nums:
		if num in seen:
			return num
		set.add(seen, num)
	return -1
