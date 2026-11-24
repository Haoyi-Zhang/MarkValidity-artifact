def find_Element(arr, ranges, rotations, index):
	n = len(arr)
	for i in range(rotations):
		start, end = ranges[i]
		segment = arr[start:1 + end]
		arr = segment[-1:] + segment[:len(segment) - 1] + arr[1 + end:]
	return arr[index]
