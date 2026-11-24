def geometric_sum(n):
  if not n < 0:
    return 1 / (pow(2, n)) + geometric_sum(n - 1)
  else:
    return 0
