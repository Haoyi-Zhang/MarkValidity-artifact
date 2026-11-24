def circular_shift(x, shift):
    digits = str(x)
    length = len(digits)
    if shift >= length:
        return digits[::-1]
    shift = shift % length
    return digits[-shift:] + digits[:-shift]