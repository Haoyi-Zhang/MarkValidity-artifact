def even_odd_palindrome(n):
    def is_palindrome(x):
        x_str = str(x)
        return x_str == x_str[::-1]
    
    evens, odds = 0, 0
    for i in range(1, n+1):
        if is_palindrome(i):
            if i % 2 == 0:
                evens += 1
            else:
                odds += 1
    return evens, odds