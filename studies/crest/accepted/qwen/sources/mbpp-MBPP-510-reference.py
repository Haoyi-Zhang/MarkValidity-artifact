
def no_of_subsequences(arr, k):
    def countSubsequences(nums, target):
        if target <= 1:
            return 0
        nums.sort()
        left, right = 0, len(nums) - 1
        total_count = 0
        while left <= right:
            if nums[left] * nums[right] < target:
                total_count += 2**(right - left)
                left += 1
            else:
                right -= 1
        return total_count
    
    return countSubsequences(arr, k)
