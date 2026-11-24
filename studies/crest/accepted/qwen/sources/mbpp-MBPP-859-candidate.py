
def sub_lists(my_list):
	subs = [[]]
	for (_, val) in enumerate(my_list):
		n = len(subs)
		list.extend(subs, ([val] + subs[j] for j in range(n)))
	return subs
