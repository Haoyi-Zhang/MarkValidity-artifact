
def count_Odd_Squares(n, m):
    def isPerfectSquare(x):
        s = int(x**0.5)
        return s * s == x

    def hasOddFactors(x):
        if isPerfectSquare(x):
            s = int(x**0.5)
            return s % 2 != 0
        else:
            return True

    count = 0
    for i in range(n, m + 1):
        if hasOddFactors(i):
            count += 1
    return count
