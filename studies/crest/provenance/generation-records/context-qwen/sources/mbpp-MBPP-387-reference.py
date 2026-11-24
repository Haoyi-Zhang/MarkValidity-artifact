
def even_or_odd(N):
    last_digit = N[-1].upper()
    if last_digit in '02468ACE':
        return "Even"
    else:
        return "Odd"
