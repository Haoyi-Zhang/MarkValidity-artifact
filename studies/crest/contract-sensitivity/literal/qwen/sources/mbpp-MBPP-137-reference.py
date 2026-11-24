
    if len(nums) == 0:
        return 0.0
    zero_count = nums.count(0)
    return round(zero_count / len(nums), 2)
