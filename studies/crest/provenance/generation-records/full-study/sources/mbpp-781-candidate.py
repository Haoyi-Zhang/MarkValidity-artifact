import math 


def count_divisors(n) : 
	count = 0
	for i in range(1, 2 + (int)(math.sqrt(n))) : 
		if (n % i == 0) : 
			count = count + 1 if ( n // i == i) else 2 + count
	return count % 2 == 0
