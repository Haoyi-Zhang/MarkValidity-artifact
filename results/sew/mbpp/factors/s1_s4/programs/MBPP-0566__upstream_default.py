def sum_digits(n):
  if not n == 0:
    return n % 10 + sum_digits(int(n / 10))
  else:
    return 0
