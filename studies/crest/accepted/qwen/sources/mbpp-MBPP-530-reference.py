
def negative_count(nums):
    negative_count = sum(1 for num in nums if num < 0)
    return round(negative_count / len(nums), 2)
