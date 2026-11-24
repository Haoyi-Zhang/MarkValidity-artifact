def shell_sort(my_list):
	gap = len(my_list) // 2
	while 0 < gap:
		for i in range(gap, len(my_list)):
			temp = my_list[i]
			j = i
			while gap <= j and temp < my_list[j - gap]:
				my_list[j] = my_list[j - gap]
				j -= gap
			my_list[j] = temp
		gap //= 2
	return my_list
