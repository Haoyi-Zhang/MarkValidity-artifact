def sequence(n):
	if n in [1, 2]:
		return 1
	seq = [0, 1, 1]
	list.extend(seq, (seq[i - seq[i - 1]] + seq[seq[i - 1]] for i in range(3, 1 + n)))
	return seq[n]
