
def validate(n):
    from collections import Counter
    count = Counter(str(n))
    return all(int(digit) >= freq for digit, freq in count.items())
