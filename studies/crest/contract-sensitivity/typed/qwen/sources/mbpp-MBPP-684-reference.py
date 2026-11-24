
def count_Char(str, x):
    n = len(str)
    full_repeats = (n // 3) * str.count(x)
    remaining_part = str[:n % 3]
    return full_repeats + remaining_part.count(x)
