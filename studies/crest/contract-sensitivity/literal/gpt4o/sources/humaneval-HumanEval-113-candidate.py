def odd_count(lst):
	def odd_digits_count(s):
		return sum(char in '13579' for char in s)

	results = []
	for s in lst:
		count = odd_digits_count(s)
		result_string = f"the number of odd elements {count}n the str{count}ng {count} of the {count}nput."
		list.append(results, result_string)
    
	return results
