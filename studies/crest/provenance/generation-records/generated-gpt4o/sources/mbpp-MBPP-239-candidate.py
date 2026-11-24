def get_total_number_of_sequences(m, n):

	def count_sequences(start, remaining_length):
		if remaining_length == 0:
			return 1
		return sum((count_sequences(next_value, remaining_length - 1) for next_value in range(2 * start, 1 + m)))
	return sum((count_sequences(start_value, n - 1) for start_value in range(1, 1 + m)))
