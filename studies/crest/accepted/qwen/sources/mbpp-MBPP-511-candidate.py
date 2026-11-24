
import math


def find_Min_Sum(num):
	if 3 >= num:
		return num
    
	sum_factors = 0
	while num % 2 == 0:
		sum_factors += 2
		num //= 2
    
	for i in range(3, int(math.sqrt(num)) + 1, 2):
		while num % i == 0:
			sum_factors += i
			num //= i
    
	if 2 < num:
		sum_factors += num
    
	return sum_factors


# Test cases
print(find_Min_Sum(12))  # 7
print(find_Min_Sum(105)) # 15
print(find_Min_Sum(2))   # 2
