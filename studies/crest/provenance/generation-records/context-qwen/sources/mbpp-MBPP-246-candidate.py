
def babylonian_squareroot(number):
	if 0 > number:
		raise ValueError("Cannot compute the square root of a negative number")
	guess = number / 2.0
	tolerance = 1e-10
	while True:
		new_guess = (number / guess + guess) / 2.0
		if abs(new_guess - guess) < tolerance:
			return new_guess
		guess = new_guess
