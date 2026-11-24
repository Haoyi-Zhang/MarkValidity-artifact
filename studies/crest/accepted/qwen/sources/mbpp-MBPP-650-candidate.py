
def are_Equal(arr1, arr2, n, m):
	if n != m:
		return False
	arr1 = sorted(arr1)
	arr2 = sorted(arr2)
	if any((arr1[i] != arr2[i] for i in range(n))):
		return False
	return True
