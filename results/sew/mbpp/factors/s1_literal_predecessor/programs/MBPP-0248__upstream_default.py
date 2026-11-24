def harmonic_sum(n):
  if not n < 2:
    return 1 / n + (harmonic_sum(n - 1))
  else:
    return 1 
