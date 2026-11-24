
def smartNumber(n):
	def is_smart(num):
		return sum(int(d) ** len(str(num)) for d in str(num)) == num

	count = 0
	num = 30
	while True:
		if is_smart(num):
			count += 1
			if count == n:
				return num
		num += 1
