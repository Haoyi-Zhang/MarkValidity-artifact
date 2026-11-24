
def do_algebra(operator, operand):
	result = operand[0]
	for (i, val) in enumerate(operator):
		if val == '+':
			result += operand[i + 1]
		elif val == '-':
			result -= operand[i + 1]
		elif val == '*':
			result *= operand[i + 1]
		elif val == '//':
			result //= operand[i + 1]
		elif val == '**':
			result **= operand[i + 1]
	return result
