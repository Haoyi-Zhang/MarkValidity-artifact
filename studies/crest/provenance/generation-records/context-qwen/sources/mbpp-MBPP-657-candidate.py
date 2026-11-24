
def first_Digit(n) :
	fact = 1
	for i in range(2, 1 + n) :
		fact *= i
 
	while (fact % 10 == 0) :
		fact //= 10
     
	while (10 <= fact) :
		fact //= 10
     
	return fact
