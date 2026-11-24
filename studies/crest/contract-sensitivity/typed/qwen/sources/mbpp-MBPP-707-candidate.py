
def count_Set_Bits(n) :
	def setBits(num):
		count = 0
		while num:
			count += num & 1
			num >>= 1
		return count

	return sum((setBits(i) for i in range(1, 1 + n)))
