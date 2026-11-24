import sys


def next_smallest_palindrome(num):
	numstr = str(num)
	return next((i for i in range(num + 1, sys.maxsize) if str(i) == str(i)[::-1]), None)
