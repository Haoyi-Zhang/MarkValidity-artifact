
def floor_Max(A,B,N):
    if A >= B:
        return N - (N // A) * A
    else:
        return B * (N // A)
