def round_and_sum(list1):
	rounded_list = [round(num) for num in list1]
	total_sum = sum(rounded_list)
	result = len(list1) * total_sum
	print(result)
