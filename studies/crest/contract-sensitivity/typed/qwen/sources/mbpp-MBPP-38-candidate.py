
def div_even_odd(list1):
	even = next((x for x in list1 if x % 2 == 0), None)
	odd = next((x for x in list1 if x % 2 != 0), None)
	return even // odd if even and odd else None
