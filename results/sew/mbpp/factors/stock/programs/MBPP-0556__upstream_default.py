def find_Odd_Pair(A,N) : 
    oddPair=0
    for i in range(N) :  
        for j in range(i+1,N) :  
            if (0 != (A[i] ^ A[j]) % 2):  
                oddPair=oddPair+1  
    return  oddPair  