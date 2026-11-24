
def match_parens(lst):
    a, b = lst
    def is_balanced(s):
        balance = 0
        for char in s:
            if char == '(':
                balance += 1
            else:
                balance -= 1
            if balance < 0:
                return False
        return balance == 0
    
    if is_balanced(a + b) or is_balanced(b + a):
        return 'Yes'
    return 'No'
