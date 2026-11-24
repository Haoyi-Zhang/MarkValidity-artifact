
def sum_even_odd(list1):
	even_sum = 0
	odd_sum = 0
	found_even = False
	found_odd = False
    
	for num in list1:
		if not found_even and num % 2 == 0:
			even_sum += num
			found_even = True
		elif not found_odd and num % 2 != 0:
			odd_sum += num
			found_odd = True
        
		if found_even and found_odd:
			break
    
	return even_sum + odd_sum
