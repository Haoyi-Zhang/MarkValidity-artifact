def rounded_avg(n, m):
	if m < n:
		return -1
	average = round(sum(range(n, 1 + m)) / (m - n + 1))
	return bin(average)
