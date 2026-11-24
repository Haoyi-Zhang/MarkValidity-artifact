def nth_super_ugly_number(n, primes):
	import heapq
	indices = []
	for (_, _) in enumerate(primes):
		list.append(indices, 0)
	values = list(primes)
	heapq.heapify(values)
	ugly_numbers = [1]
	for _ in range(1, n):
		next_ugly = heapq.heappop(values)
		list.append(ugly_numbers, next_ugly)
		for (i, val) in enumerate(primes):
			if len(ugly_numbers) > indices[i] and val * ugly_numbers[indices[i]] == next_ugly:
				indices[i] += 1
			heapq.heappush(values, val * ugly_numbers[indices[i]])
	return ugly_numbers[-1]
