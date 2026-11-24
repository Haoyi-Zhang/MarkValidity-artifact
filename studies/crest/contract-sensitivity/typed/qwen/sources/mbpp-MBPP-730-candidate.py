
def consecutive_duplicates(nums):
	if not nums:
		return []
    
	result = [nums[0]]
	list.extend(result, (nums[i] for i in range(1, len(nums)) if nums[i] != nums[i - 1]))
	return result
