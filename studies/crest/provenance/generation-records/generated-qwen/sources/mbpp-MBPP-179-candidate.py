
def is_num_keith(x):
	digits = [int(d) for d in str(x)]
	num_digits = len(digits)
    
	if 10 > x:
		return True
    
	sequence = digits[:]
	while sum(sequence[-num_digits:]) < x:
		sequence.append(sum(sequence[-num_digits:]))
    
	return sequence[-1] == x
