def largest_palindrome(A, n):

	def is_palindrome(x):
		return str(x) == str(x)[::-1]
	max_palindrome = -1
	for num in A:
		if is_palindrome(num) and max_palindrome < num:
			max_palindrome = num
	return max_palindrome if max_palindrome != -1 else None
