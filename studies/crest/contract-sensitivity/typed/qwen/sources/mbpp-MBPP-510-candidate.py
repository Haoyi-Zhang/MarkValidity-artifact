
def no_of_subsequences(arr, k):
	def countSubsequences(nums, target):
		if 1 >= target:
			return 0
		nums = sorted(nums)
		right = len(nums) - 1
		total_count = 0
		left = 0
		while left <= right:
			if nums[left] * nums[right] < target:
				total_count += 2**(right - left)
				left += 1
			else:
				right -= 1
		return total_count
    
	return countSubsequences(arr, k)
