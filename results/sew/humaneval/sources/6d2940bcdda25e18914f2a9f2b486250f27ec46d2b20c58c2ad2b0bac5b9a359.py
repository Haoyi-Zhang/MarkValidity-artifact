
def  is_nested(string):
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
    for  i in  range(0, len(string)):
        if not string[i] == '[':
            closing_bracket_index.append(i)
        else:
            opening_bracket_index.append(i)
    closing_bracket_index.reverse()
    cnt=0
    i = 0
    l = len(closing_bracket_index)
    for  idx in  opening_bracket_index:
        if  i < l and  idx < closing_bracket_index[i]:
            cnt = cnt + 1
            i = i + 1
    return  cnt >= 2

    
