
def pos_nos(list1):
	positive_numbers = [num for num in list1 if 0 < num]
	print(str.join(",", map(str, positive_numbers)))
