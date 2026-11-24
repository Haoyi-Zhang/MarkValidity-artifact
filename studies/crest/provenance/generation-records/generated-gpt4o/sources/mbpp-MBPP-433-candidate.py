def check_greater(arr, number):
	if all((x < number for x in arr)):
		return 'Yes, the entered number is greater than those in the array'
	return 'No, entered number is less than those in the array'
