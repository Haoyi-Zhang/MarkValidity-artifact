
def positive_count(nums):
    count = sum(1 for num in nums if num > 0)
    return round(count / len(nums), 2)
