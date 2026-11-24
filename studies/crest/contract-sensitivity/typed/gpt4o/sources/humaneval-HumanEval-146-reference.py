def specialFilter(nums):
    def is_odd_digit(digit):
        return digit in "13579"
    
    def has_odd_first_and_last_digits(num):
        num_str = str(abs(num))
        return is_odd_digit(num_str[0]) and is_odd_digit(num_str[-1])

    return sum(1 for num in nums if num > 10 and has_odd_first_and_last_digits(num))