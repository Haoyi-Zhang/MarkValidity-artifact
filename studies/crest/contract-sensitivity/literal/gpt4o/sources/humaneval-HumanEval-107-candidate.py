def even_odd_palindrome(n):
	def is_palindrome(x):
		x_str = str(x)
		return x_str == x_str[::-1]
    
	evens = 0
	odds = 0
	for i in range(1, 1 + n):
		if is_palindrome(i):
			if i % 2 == 0:
				evens += 1
			else:
				odds += 1
	return evens, odds
