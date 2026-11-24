
def palindrome_lambda(texts):
	return list(filter(lambda x: x == x[::-1], texts))
