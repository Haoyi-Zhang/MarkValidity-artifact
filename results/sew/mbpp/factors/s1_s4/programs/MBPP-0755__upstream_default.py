def second_smallest(numbers):
  unique_numbers = list(set(numbers))
  unique_numbers.sort()
  if not len(unique_numbers) < 2:
    return unique_numbers[1]
  else:
    return None
