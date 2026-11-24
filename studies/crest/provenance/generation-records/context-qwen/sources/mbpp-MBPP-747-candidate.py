
def lcs_of_three(X, Y, Z, m, n, o):
	if m == 0 or n == 0 or o == 0:
		return 0
	if X[m - 1] == Y[n - 1] and X[m - 1] == Z[o - 1]:
		return lcs_of_three(X, Y, Z, m - 1, n - 1, o - 1) + 1
	return max(max(lcs_of_three(X, Y, Z, m, n - 1, o), lcs_of_three(X, Y, Z, m - 1, n, o)), lcs_of_three(X, Y, Z, m, n, o - 1))
