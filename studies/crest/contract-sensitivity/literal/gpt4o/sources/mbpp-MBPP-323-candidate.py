def re_arrange(arr, n):
	pos = [x for x in arr if 0 <= x]
	neg = [x for x in arr if 0 > x]
	i = 0
	j = 0
	result = []
	while i < len(pos) and len(neg) > j:
		list.extend(result, [neg[j], pos[i]])
		i += 1
		j += 1
	while len(neg) > j:
		list.append(result, neg[j])
		j += 1
	while i < len(pos):
		list.append(result, pos[i])
		i += 1
	return result
