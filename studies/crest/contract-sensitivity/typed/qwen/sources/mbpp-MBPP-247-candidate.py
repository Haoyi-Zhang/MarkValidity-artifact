
def lps(str1):
	n = len(str1)
	L = [[0 for _ in range(n)] for y in range(n)]
 
	for i in range(n):
		L[i][i] = 1
 
	for cl in range(2, 1 + n):
		for i in range(n - cl + 1):
			j = i + cl - 1
			L[i][j] = 2 if str1[i] == str1[j] and cl == 2 else (L[i + 1][j - 1] + 2 if str1[i] == str1[j] else max(L[i][j - 1], L[i + 1][j]))
 
	return L[0][n - 1]
