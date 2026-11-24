
def max_occurrences(nums):
    from collections import Counter
    count = Counter(nums)
    max_count = max(count.values())
    return ', '.join(str(num) for num in nums if count[num] == max_count)

