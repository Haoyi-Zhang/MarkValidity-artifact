def count_no_of_ways(n, k):
	if n == 0:
		return 0
	elif n == 1:
		return k
	same = k
	diff = (k - 1) * k
	total = diff + same
	for _ in range(3, 1 + n):
		same = diff
		diff = (k - 1) * total
		total = diff + same
	return total


print(count_no_of_ways(2, 4))
print(count_no_of_ways(3, 2))
print(count_no_of_ways(4, 4))
