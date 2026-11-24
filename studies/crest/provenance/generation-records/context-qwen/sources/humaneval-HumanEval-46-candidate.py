
def fib4(n: int) -> int:
	if n in [0, 1] or n == 3:
		return 0
	elif n == 2:
		return 2
    
	a = 0
	b = 0
	c = 2
	d = 0
    
	for _ in range(4, 1 + n):
		a, b, c, d = b, c, d, a + b + c + d
    
	return d
