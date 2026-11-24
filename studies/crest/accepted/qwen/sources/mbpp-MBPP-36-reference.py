
def find_Nth_Digit(p, q, N):
    # Calculate the integer part of the fraction
    integer_part = p // q
    
    # Subtract the product of the integer part and denominator from the numerator
    remainder = p % q
    
    # If N is less than or equal to 0 return the corresponding digit of the integer part
    if N <= len(str(integer_part)):
        return int(str(integer_part)[N-1])
    
    # Initialize a variable to keep track of the number of digits found in the decimal part
    num_decimal_digits = len(str(integer_part))
    
    # Loop until we find the nth digit in the decimal part
    while True:
        # Multiply the remainder by 10 to shift the decimal point one place to the right
        remainder *= 10
        
        # Calculate the next digit in the decimal part
        digit = remainder // q
        
        # If N is less than or equal to num_decimal_digits + 1, return the corresponding digit
        if N <= num_decimal_digits + 1:
            return digit
        
        # Update the remainder and increment num_decimal_digits
        remainder %= q
        num_decimal_digits += 1
