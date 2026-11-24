
def fruit_distribution(s,n):
    import re
    numbers = list(map(int, re.findall(r'\d+', s)))
    return n - sum(numbers)
