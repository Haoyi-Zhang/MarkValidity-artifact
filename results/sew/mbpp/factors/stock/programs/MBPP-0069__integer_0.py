def is_sublist(l, s):
	sub_set = False
	if  s == list():
		sub_set=True
	elif  l == s:
		sub_set=True
	elif  len(s)>len(l):
		sub_set=False
	else:
		for  i in  range(0, len(l)):
			if  s[0] == l[i]:
				n=1
				while (n<len(s)) and (s[n] == l[i+n]):
					n += 1				
				if n==len(s):
					sub_set=True
	return  sub_set