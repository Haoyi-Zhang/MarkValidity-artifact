
import math

def find_Min_Sum(num):
    if num <= 3:
        return num
    
    sum_factors = 0
    while num % 2 == 0:
        sum_factors += 2
        num //= 2
    
    for i in range(3, int(math.sqrt(num)) + 1, 2):
        while num % i == 0:
            sum_factors += i
            num //= i
    
    if num > 2:
        sum_factors += num
    
    return sum_factors

# Test cases
print(find_Min_Sum(12))  # 7
print(find_Min_Sum(105)) # 15
print(find_Min_Sum(2))   # 2
