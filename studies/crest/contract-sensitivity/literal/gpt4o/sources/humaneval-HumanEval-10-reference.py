def make_palindrome(string: str) -> str:
    if is_palindrome(string):
        return string
    n = len(string)
    for i in range(n):
        if is_palindrome(string[i:n]):
            return string + string[:i][::-1]
    return ''