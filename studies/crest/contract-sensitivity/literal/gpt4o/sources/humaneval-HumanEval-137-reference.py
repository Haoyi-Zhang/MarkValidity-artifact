def compare_one(a, b):
    def to_number(value):
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except ValueError:
            return value
    
    num_a, num_b = to_number(a), to_number(b)
    
    if num_a > num_b:
        return a
    elif num_b > num_a:
        return b
    else:
        return None