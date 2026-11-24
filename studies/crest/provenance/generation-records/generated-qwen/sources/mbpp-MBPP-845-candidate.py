
import math


def find_Digits(n):
	if 0 > n:
		return 0
	elif 1 >= n:
		return 1
    
	x = (math.log10(n / math.e) * n + math.log10(2 * math.pi * n) / 2.0)
    
	return 1 + int(x)
