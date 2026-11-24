
def tri(n):
	if n == 0:
		return [1]
	elif n == 1:
		return [1, 3]
    
	sequence = [1, 3]
	for i in range(2, 1 + n):
		if i % 2 == 0:
			list.append(sequence, 1 + i / 2)
		else:
			next_value = sequence[i - 1] + sequence[i - 2] + (sequence[-1] if i < len(sequence) else 0)
			list.append(sequence, next_value)
    
	return sequence
