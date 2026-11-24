
def get_total_number_of_sequences(m, n):
    def count_sequences(current, length):
        if length == n:
            return 1
        total = 0
        for next_value in range(2 * current, m + 1):
            total += count_sequences(next_value, length + 1)
        return total
    
    total_sequences = 0
    for start in range(1, m + 1):
        total_sequences += count_sequences(start, 1)
    
    return total_sequences
