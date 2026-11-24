
def largest_palindrome(A, n): 
	max_palindrome = -1
	for i in range(n):
		num = A[i]
		if str(num) == str(num)[::-1] and max_palindrome < num:
			max_palindrome = num
	return max_palindrome
