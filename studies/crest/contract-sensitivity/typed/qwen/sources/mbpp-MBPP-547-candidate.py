
def Total_Hamming_Distance(n):
	total_distance = 0
	for i in range(1 + n):
		for j in range(i + 1, 1 + n):
			total_distance += bin(i ^ j).count('1')
	return total_distance
