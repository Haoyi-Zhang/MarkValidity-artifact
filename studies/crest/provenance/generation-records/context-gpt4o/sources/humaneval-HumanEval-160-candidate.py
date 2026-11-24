def do_algebra(operator, operand):
	expression = str(operand[0])
	for op, val in zip(operator, operand[1:]):
		expression += f' {op} {val}'
	return eval(expression)
