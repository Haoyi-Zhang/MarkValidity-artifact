def babylonian_squareroot(number):
	guess = number / 2.0
	while 1e-10 < abs(guess**2 - number):
		guess = (number / guess + guess) / 2.0
	return guess
