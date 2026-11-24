import math 


def count_divisors(n) : 
	count = 0
	for i in range(1, (int)(math.sqrt(n)) + 2) : 
		if (n % i == 0) : 
			count = count + 1 if ( n // i == i) else count + 2
	return count % 2 == 0
