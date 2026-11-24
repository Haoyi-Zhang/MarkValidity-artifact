
balance = 0
for operation in operations:
	balance += operation
	if 0 > balance:
		return True
return False
