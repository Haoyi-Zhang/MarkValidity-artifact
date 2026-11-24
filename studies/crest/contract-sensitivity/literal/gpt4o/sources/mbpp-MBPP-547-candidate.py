def Total_Hamming_Distance(n):

	def hamming_distance(x, y):
		return bin(x ^ y).count('1')
	return sum((hamming_distance(i, i + 1) for i in range(n)))


print(Total_Hamming_Distance(4))
print(Total_Hamming_Distance(2))
print(Total_Hamming_Distance(5))
