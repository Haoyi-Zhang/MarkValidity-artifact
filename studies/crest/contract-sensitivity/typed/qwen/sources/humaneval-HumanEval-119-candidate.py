
def match_parens(lst):
	a, b = lst

	def is_balanced(s):
		balance = 0
		for char in s:
			if char == '(':
				balance += 1
			else:
				balance -= 1
			if 0 > balance:
				return False
		return balance == 0
    
	if is_balanced(a + b) or is_balanced(a + b):
		return 'Yes'
	return 'No'
