def correct_bracketing(brackets: str):
	balance = 0
	for bracket in brackets:
		if bracket == "(":
			balance += 1
		elif bracket == ")":
			balance -= 1
		if 0 > balance:
			return False
	return balance == 0
