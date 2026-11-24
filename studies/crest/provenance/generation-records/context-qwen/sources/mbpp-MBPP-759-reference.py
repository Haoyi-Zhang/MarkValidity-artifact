
def is_decimal(num):
    try:
        float(num)
        parts = num.split('.')
        return len(parts) == 2 and len(parts[1]) <= 2
    except ValueError:
        return False
