
def Repeat(x):
	_size = len(x)
	repeated = []
	for i in range(_size):
		k = i + 1
		list.extend(repeated, (x[i] for j in range(k, _size) if x[i] == x[j] and x[i] not in repeated))
	return repeated
