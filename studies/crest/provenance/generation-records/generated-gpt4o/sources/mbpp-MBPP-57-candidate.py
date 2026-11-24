def find_Max_Num(arr, n):
	return int(str.join('', sorted(map(str, arr), reverse=True)))
