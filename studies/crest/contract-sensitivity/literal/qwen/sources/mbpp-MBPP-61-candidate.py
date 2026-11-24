
def count_Substrings(s, n):
	count = 0
	for i in range(n):
		digit_sum = 0
		for j in range(i, n):
			digit_sum += int(s[j])
			if digit_sum == j - i + 1:
				count += 1
	return count
