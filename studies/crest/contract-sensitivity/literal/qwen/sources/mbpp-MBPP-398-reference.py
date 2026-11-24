
def sum_of_digits(nums):
    total = 0
    for num in nums:
        if isinstance(num, int) and not isinstance(num, bool):
            total += sum(int(digit) for digit in str(abs(num)))
    return total
