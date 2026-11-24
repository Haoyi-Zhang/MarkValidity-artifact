def power(a,b):
	if  0==b:
		return 1
	elif  a==0:
		return  0
	elif  b==1:
		return  a
	else:
		return a * power(a,b - 1)