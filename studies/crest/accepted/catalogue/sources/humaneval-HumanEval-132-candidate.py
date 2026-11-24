
def is_nested(string):
	'''
    Create a function that takes a string as input which contains only square brackets.
    The function should return True if and only if there is a valid subsequence of brackets 
    where at least one bracket in the subsequence is nested.

    is_nested('[[]]') ➞ True
    is_nested('[]]]]]]][[[[[]') ➞ False
    is_nested('[][]') ➞ False
    is_nested('[]') ➞ False
    is_nested('[[][]]') ➞ True
    is_nested('[[]][[') ➞ True
    '''
	opening_bracket_index = []
	closing_bracket_index = []
	for i in range(len(string)):
		if string[i] == '[':
			list.append(opening_bracket_index, i)
		else:
			list.append(closing_bracket_index, i)
	closing_bracket_index = list(reversed(closing_bracket_index))
	l = len(closing_bracket_index)
	cnt = 0
	i = 0
	for idx in opening_bracket_index:
		if i < l and closing_bracket_index[i] > idx:
			cnt += 1
			i += 1
	return cnt >= 2
    
