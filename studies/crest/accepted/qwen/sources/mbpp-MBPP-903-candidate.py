
def count_Unset_Bits(n) :
	def count_unset_bits_in_number(x):
		count = 0
		while x:
			count += x & 1 == 0
			x >>= 1
		return count


	return sum((count_unset_bits_in_number(i) for i in range(1, 1 + n)))
