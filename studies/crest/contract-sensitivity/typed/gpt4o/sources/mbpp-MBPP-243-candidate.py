def sort_on_occurence(lst):
	from collections import defaultdict
	d = defaultdict(list)
	for k, v in lst:
		d[k].append(v)
	result = []
	list.extend(result, ((k, *v, len(v)) for k, v in sorted(d.items())))
	return result
