
def neg_nos(list1):
	negative_numbers = [str(num) for num in list1 if 0 > num]
	print(str.join(",", negative_numbers))
