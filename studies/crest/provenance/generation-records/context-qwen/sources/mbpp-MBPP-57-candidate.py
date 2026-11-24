
def find_Max_Num(arr, n) :
	arr = sorted(arr, reverse=True)
	return int(str.join('', map(str, arr)))
