def modular_inverse(arr, N, P):
	return sum((pow(num, P - 2, P) == num % P for num in arr))
