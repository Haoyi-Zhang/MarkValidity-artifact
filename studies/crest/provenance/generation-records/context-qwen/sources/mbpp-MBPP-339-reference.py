
def find_Divisor(x, y):
    def count_divisors(n):
        return sum(1 for i in range(1, n + 1) if n % i == 0)
    
    max_divisor_count = 0
    result = None
    
    for num in range(x, y + 1):
        divisor_count = count_divisors(num)
        if divisor_count > max_divisor_count:
            max_divisor_count = divisor_count
            result = num
    
    return result
