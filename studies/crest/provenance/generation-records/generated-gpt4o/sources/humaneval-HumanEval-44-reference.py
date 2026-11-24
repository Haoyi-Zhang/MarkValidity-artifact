def change_base(x: int, base: int):
    if base <= 1 or base > 9:
        raise ValueError("Base must be between 2 and 9")
    result = ''
    while x > 0:
        remainder = x % base
        result = str(remainder) + result
        x = x // base
    return result if result else '0'