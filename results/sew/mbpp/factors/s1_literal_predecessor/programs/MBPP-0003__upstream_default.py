import  math
def is_not_prime(n):
    result=False
    for i in range(2,1 + int(math.sqrt(n))):
        if n % i == 0:
            result = True
    return result