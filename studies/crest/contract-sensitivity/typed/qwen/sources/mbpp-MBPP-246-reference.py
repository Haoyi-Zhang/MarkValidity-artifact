
def babylonian_squareroot(number):
    if number < 0:
        raise ValueError("Cannot compute the square root of a negative number")
    tolerance = 1e-10
    guess = number / 2.0
    while True:
        new_guess = (guess + number / guess) / 2.0
        if abs(new_guess - guess) < tolerance:
            return new_guess
        guess = new_guess
