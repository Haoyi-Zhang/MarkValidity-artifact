
def odd_Num_Sum(n) :
	sum = 0
	for i in range(n):
		num = i * 2 + 1
		sum += num ** 5
	return sum
