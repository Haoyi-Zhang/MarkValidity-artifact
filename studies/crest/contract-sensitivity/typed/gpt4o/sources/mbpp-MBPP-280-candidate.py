def sequential_search(dlist, item):
	return next(((True, index) for index, value in enumerate(dlist) if value == item), (False, -1))
