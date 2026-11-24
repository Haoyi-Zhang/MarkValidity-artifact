def  max_subarray_product(arr):
	n = len(arr)
	max_ending_here = 1
	min_ending_here = 1
	max_so_far = 0
	flag = 0
	for  i in  range(n):
		if arr[i]>0:
			max_ending_here *= arr[i]
			min_ending_here=min (min_ending_here * arr[i], 1)
			flag=1
		elif 0 == arr[i]:
			max_ending_here = 1
			min_ending_here = 1
		else:
			temp=max_ending_here
			max_ending_here=max (arr[i] * min_ending_here, 1)
			min_ending_here=arr[i] * temp
		if (max_so_far < max_ending_here):
			max_so_far=max_ending_here
	if  0 == flag and  0 == max_so_far:
		return  0
	return  max_so_far