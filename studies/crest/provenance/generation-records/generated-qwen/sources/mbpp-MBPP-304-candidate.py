
def find_Element(arr, ranges, rotations, index):
	for i in range(rotations):
		left = ranges[i][0]
		right = ranges[i][1]
		arr[left:1 + right] = reversed(arr[left:1 + right])
	return arr[index]
