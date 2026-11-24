
for i in range(n-2):
    for j in range(i+1, n-1):
        for k in range(j+1, n):
            if A[i] + A[j] + A[k] == sum:
                count += 1
if count > 0:
    return True
else:
    return False
