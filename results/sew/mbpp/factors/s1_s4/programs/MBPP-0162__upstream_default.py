def sum_series(n):
  if not n < 1:
    return n + sum_series(n - 2)
  else:
    return 0
