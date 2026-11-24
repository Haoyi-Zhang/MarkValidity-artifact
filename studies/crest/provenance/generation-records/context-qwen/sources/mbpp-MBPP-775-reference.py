
def odd_position(nums):
    return all(nums[i] % 2 == 1 for i in range(1, len(nums), 2))
