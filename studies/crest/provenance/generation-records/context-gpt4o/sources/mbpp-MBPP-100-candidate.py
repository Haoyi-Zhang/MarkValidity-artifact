def next_smallest_palindrome(num):
	num_str = str(1 + num)
	length = len(num_str)
	half_length = length // 2
	if length % 2 == 0:
		left_half = num_str[:half_length]
		possible_palindrome = int(left_half + left_half[::-1])
	else:
		left_half = num_str[:half_length + 1]
		possible_palindrome = int(left_half[-2::-1] + left_half)
	if possible_palindrome > num:
		return possible_palindrome
	left_half = str(int(left_half) + 1)
	if length % 2 == 0:
		return int(left_half + left_half[::-1])
	return int(left_half[-2::-1] + left_half)
