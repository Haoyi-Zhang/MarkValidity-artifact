

def fib(n: int):
    """Return n-th Fibonacci number.
    >>> fib(10)
    55
    >>> fib(1)
    1
    >>> fib(8)
    21
    """
    if  0 == n:
        return  0
    if  1 == n:
        return  1
    return  fib(n - 1) + fib(n - 2)
