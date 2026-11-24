
def get_total_number_of_sequences(m, n):
	def count_sequences(current, length):
		if length == n:
			return 1
		return sum((count_sequences(next_value, 1 + length) for next_value in range(2 * current, 1 + m)))
    
    
	return sum((count_sequences(start, 1) for start in range(1, 1 + m)))
