
def average_tuple(nums):
    return [sum(row[i] for row in nums) / len(nums) for i in range(len(nums[0]))]
