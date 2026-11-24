def find_Element(arr, ranges, rotations, index) :  
	for i in range(rotations - 1, -1, -1 ) : 
		left = ranges[i][0] 
		right = ranges[i][1] 
		if (left <= index and right >= index) : 
			index = right if (index == left) else index - 1
	return arr[index]
