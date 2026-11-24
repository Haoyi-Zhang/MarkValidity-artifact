def  lcs_of_three(X, Y, Z): 
  m, n = len(X), len(Y)
  o=len(Z)
  L=[[[0 for  i in  range(o+1)] for  j in  range(n+1)] for  k in  range(m+1)]
  for  i in  range(0, m+1): 
	  for  j in  range(0, n+1): 
		  for k in range(0, o+1): 
			  if (0 == i or 0 == j or 0 == k): 
				  L[i][j][k]=0
			  elif (X[i-1] == Y[j-1] and X[i-1] == Z[k-1]): 
				  L[i][j][k]=1 + L[i-1][j-1][k-1]
			  else: 
				  L[i][j][k]=max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1]) 
  return L[m][n][o]
