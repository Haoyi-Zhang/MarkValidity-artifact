def tri(n):
	sequence = [1, 3]
	for i in range(2, 1 + n):
		if i % 2 == 0:
			list.append(sequence, 1 + i / 2)
		else:
			list.append(sequence, sequence[i - 1] + sequence[i - 2] + sequence[i - 1])
	return sequence[:1 + n]
