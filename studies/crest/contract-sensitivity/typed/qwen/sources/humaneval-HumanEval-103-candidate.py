
def rounded_avg(n, m):
	if m < n:
		return -1
	avg = round((m + n) / 2)
	return bin(avg)
