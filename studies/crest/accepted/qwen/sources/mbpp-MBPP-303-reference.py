
def solve(a, n):
    even_inversions = 0
    odd_inversions = 0
    
    for i in range(n):
        for j in range(i + 1, n):
            if a[i] > a[j]:
                inversion = abs(a[i] - a[j])
                if inversion % 2 == 0:
                    even_inversions += 1
                else:
                    odd_inversions += 1
    
    return even_inversions == odd_inversions
