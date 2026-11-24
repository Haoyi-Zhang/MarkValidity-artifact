
def cal_sum(n):
	if 3 > n:
		return n
	perrin = [3, 0, 2]
	list.extend(perrin, (perrin[i - 2] + perrin[i - 3] for i in range(3, n)))
	return sum(perrin)
