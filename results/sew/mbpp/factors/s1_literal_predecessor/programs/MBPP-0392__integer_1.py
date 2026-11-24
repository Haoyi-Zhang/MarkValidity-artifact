def  get_max_sum (n):
	res=[]
	res.append(0)
	res.append(1)
	i=2
	while i < 1 + n:
		res.append(max(i, (res[int(i / 2)] 
						+ res[int(i / 3)] +
							res[int(i / 4)]
						+ res[int(i / 5)])))
		i = i + 1
	return res[n]
